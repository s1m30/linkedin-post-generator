from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PassphraseSubmit(BaseModel):
    passphrase: str


class PublicConfigResponse(BaseModel):
    supabase_url: str
    supabase_anon_key: str
