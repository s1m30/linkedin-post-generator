import subprocess
import logging

logger = logging.getLogger(__name__)

def send_notification(title: str, message: str):
    """
    Sends a local Windows notification using PowerShell.
    First tries to send a modern Win10/11 toast notification.
    If that fails (due to environment/permissions), falls back to a tray balloon notification.
    """
    # Escape single quotes for PowerShell scripting
    title_esc = title.replace("'", "''")
    msg_esc = message.replace("'", "''")

    # Script details: Try modern ToastNotification manager, fallback to Forms.NotifyIcon balloon tip
    powershell_script = f"""
    try {{
        # Load necessary assemblies
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
        [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null

        $Template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $Xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($Template)
        $Xml.GetElementsByTagName('text').Item(0).AppendChild($Xml.CreateTextNode('{title_esc}')) | Out-Null
        $Xml.GetElementsByTagName('text').Item(1).AppendChild($Xml.CreateTextNode('{msg_esc}')) | Out-Null
        $Xml.DocumentElement.SetAttribute('launch', 'http://127.0.0.1:8000') | Out-Null

        $Toast = [Windows.UI.Notifications.ToastNotification]::new($Xml)
        $AppId = 'LinkedIn Post Generator'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId).Show($Toast)
    }} catch {{
        # Fallback balloon notification
        [void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
        $notification = New-Object System.Windows.Forms.NotifyIcon
        $notification.Icon = [System.Drawing.SystemIcons]::Information
        $notification.BalloonTipTitle = '{title_esc}'
        $notification.BalloonTipText = '{msg_esc}'
        $notification.Visible = $true
        $notification.ShowBalloonTip(5000)
        Start-Sleep -s 3
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_script],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Windows notification triggered for post: {title}")
    except Exception as e:
        logger.error(f"Failed to send Windows notification: {e}")
        # Secondary fallback: simple console logging
        print(f"\n[Notification Alert]\nTitle: {title}\nMessage: {message}\n")
