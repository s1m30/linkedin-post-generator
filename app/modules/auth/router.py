from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from core.config import settings
from modules.auth.dependencies import get_current_user
from modules.auth.models import Profile
from modules.auth.schemas import ProfileResponse, PassphraseSubmit, PublicConfigResponse
from modules.auth.service import AuthService

router = APIRouter(prefix="/api")


@router.get("/config", response_model=PublicConfigResponse)
def get_public_config():
    """
    Public, unauthenticated: the frontend needs these to initialize the
    Supabase client before a user has signed in. Both values are safe to
    expose client-side (the anon key is designed for this).
    """
    return PublicConfigResponse(
        supabase_url=settings.SUPABASE_URL,
        supabase_anon_key=settings.SUPABASE_ANON_KEY,
    )


@router.get("/auth/me", response_model=ProfileResponse)
def get_me(current_user: Profile = Depends(get_current_user)):
    return current_user


@router.post("/auth/approve", response_model=ProfileResponse)
def approve(
    submission: PassphraseSubmit,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return AuthService.approve_profile(db, user_id=current_user.id, passphrase=submission.passphrase)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
