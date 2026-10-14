import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from database.session import SessionLocal
from modules.posts.service import PostService
from modules.scheduler.notifier import send_notification

logger = logging.getLogger(__name__)

# Single instance of the background scheduler.
# All scheduled_time values are stored as naive UTC (see Post model / datetime.utcnow() usage),
# so the scheduler must interpret naive datetimes as UTC too, not the host's local timezone.
scheduler = BackgroundScheduler(timezone="UTC")

async def run_generation_task(post_id: int):
    """
    The actual asynchronous generation task.
    """
    logger.info(f"Starting background post generation for post ID: {post_id}")
    db: Session = SessionLocal()
    try:
        # Generates content and updates status to completed/failed
        post = await PostService.generate_post_content(db, post_id)
        
        # Send native Windows notification
        notification_title = f"LinkedIn Post Generated!"
        notification_msg = f"Your scheduled post '{post.title or 'No Title'}' is ready to review."
        send_notification(notification_title, notification_msg)
        
        logger.info(f"Successfully generated scheduled post ID: {post_id}")
    except Exception as e:
        logger.error(f"Error in background task for post ID {post_id}: {e}")
        PostService.update_post_status(db, post_id, "failed")
    finally:
        db.close()

def schedule_post_job(post_id: int, run_time: datetime):
    """
    Schedules a date-based trigger for post generation.
    Wraps the async execution safely for APScheduler's thread pool.
    """
    job_id = f"post_{post_id}"

    def sync_wrapper():
        try:
            # Set up a new event loop inside this background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_generation_task(post_id))
            finally:
                loop.close()
        except Exception as ex:
            logger.error(f"Failed to run scheduled job wrapper for post {post_id}: {ex}")

    # Remove existing job if it is being rescheduled
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        sync_wrapper,
        trigger=DateTrigger(run_date=run_time, timezone="UTC"),
        id=job_id,
        # Default misfire_grace_time is 1 second; if the process was briefly delayed
        # (system load, sleep/wake, slow startup) the job would otherwise be silently
        # skipped instead of run. None means always run no matter how late.
        misfire_grace_time=None
    )
    logger.info(f"Post {post_id} scheduled to generate at {run_time} (UTC)")

def load_scheduled_posts():
    """
    Scans the database for posts with 'scheduled' status and queues them.
    Used on application startup.
    """
    db = SessionLocal()
    try:
        from modules.posts.models import Post
        now = datetime.utcnow()
        # Find posts that are scheduled and set in the future
        scheduled_posts = db.query(Post).filter(
            Post.status == "scheduled",
            Post.scheduled_time > now
        ).all()

        for post in scheduled_posts:
            schedule_post_job(post.id, post.scheduled_time)
            
        logger.info(f"Loaded {len(scheduled_posts)} scheduled posts from database on startup.")
    except Exception as e:
        logger.error(f"Error loading scheduled posts on startup: {e}")
    finally:
        db.close()
