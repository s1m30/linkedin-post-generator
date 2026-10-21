from uuid import UUID
from sqlalchemy.orm import Session

from modules.auth.models import Profile
from modules.auth.security import verify_passphrase


class AuthService:
    @staticmethod
    def get_or_create_profile(db: Session, user_id: UUID, email: str) -> Profile:
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if profile:
            return profile
        profile = Profile(id=user_id, email=email, is_approved=False)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def approve_profile(db: Session, user_id: UUID, passphrase: str) -> Profile:
        if not verify_passphrase(passphrase):
            raise ValueError("Incorrect passphrase")

        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if not profile:
            raise ValueError("Profile not found")

        profile.is_approved = True
        db.commit()
        db.refresh(profile)
        return profile
