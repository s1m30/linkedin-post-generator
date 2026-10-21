import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Uuid
from datetime import datetime
from database.session import Base


class Profile(Base):
    """
    Mirrors a Supabase auth.users row. The id is the same UUID Supabase
    assigns on sign-in; this table only tracks app-level authorization
    (whether the invite passphrase has been entered) and is the FK target
    for per-user data (posts, style templates).
    """
    __tablename__ = "profiles"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True, index=True)
    is_approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
