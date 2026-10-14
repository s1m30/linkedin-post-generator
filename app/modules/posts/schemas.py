from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# Style Template schemas
class StyleTemplateBase(BaseModel):
    name: str
    content: str

class StyleTemplateCreate(StyleTemplateBase):
    pass

class StyleTemplateResponse(StyleTemplateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Post schemas
class PostBase(BaseModel):
    title: Optional[str] = None
    type: str = Field("post", pattern="^(post|carousel)$")
    rough_draft: Optional[str] = None
    web_sources: Optional[List[str]] = None
    auto_search_count: Optional[int] = Field(None, ge=1, le=20)
    style_template_id: Optional[int] = None
    scheduled_time: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class PostRefine(BaseModel):
    instruction: str

class PostResponse(BaseModel):
    id: int
    title: Optional[str] = None
    type: str
    rough_draft: Optional[str] = None
    web_sources: Optional[List[str]] = None
    auto_search_count: Optional[int] = None
    style_template_id: Optional[int] = None
    content: Optional[str] = None
    status: str
    scheduled_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PostSchedule(BaseModel):
    scheduled_time: datetime
