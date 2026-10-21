import logging
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.session import get_db
from modules.auth.models import Profile
from modules.auth.security import verify_supabase_jwt, InvalidTokenError
from modules.auth.service import AuthService

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Profile:
    """
    Verifies the Supabase access token on every request and upserts a local
    Profile row on first sight. Does NOT require is_approved - use
    require_approved_user for routes that need the passphrase gate passed.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication token")

    try:
        claims = verify_supabase_jwt(credentials.credentials)
        user_id = UUID(claims["sub"])
    except (InvalidTokenError, ValueError) as e:
        logger.warning("Rejected auth token: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return AuthService.get_or_create_profile(db, user_id=user_id, email=claims["email"])


def require_approved_user(current_user: Profile = Depends(get_current_user)) -> Profile:
    if not current_user.is_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending invite passphrase")
    return current_user
