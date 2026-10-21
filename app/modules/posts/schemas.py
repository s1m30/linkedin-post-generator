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
    mode: str = Field("generate", pattern="^(generate|assist)$")
    rough_draft: Optional[str] = None
    additional_context: Optional[str] = None
    web_sources: Optional[List[str]] = None
    auto_search_count: Optional[int] = Field(None, ge=1, le=20)
    style_template_id: Optional[int] = None
    scheduled_time: Optional[datetime] = None

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    rough_draft: Optional[str] = None
    additional_context: Optional[str] = None
    web_sources: Optional[List[str]] = None
    auto_search_count: Optional[int] = Field(None, ge=1, le=20)
    style_template_id: Optional[int] = None

class PostRefine(BaseModel):
    instruction: str

# Assist mode schemas
class AssistFactCheckItem(BaseModel):
    claim: str
    verdict: str  # "supported" | "unsupported" | "unverified" | "conflicting"
    note: str
    source: Optional[str] = None

class AssistSuggestion(BaseModel):
    type: str  # "add" | "modify" | "remove"
    detail: str

class AssistResult(BaseModel):
    fact_check: List[AssistFactCheckItem] = []
    structured_draft: str = ""
    suggestions: List[AssistSuggestion] = []
    template: str = ""

class PostResponse(BaseModel):
    id: int
    title: Optional[str] = None
    type: str
    mode: str
    rough_draft: Optional[str] = None
    additional_context: Optional[str] = None
    web_sources: Optional[List[str]] = None
    auto_search_count: Optional[int] = None
    style_template_id: Optional[int] = None
    content: Optional[str] = None
    assist_result: Optional[AssistResult] = None
    status: str
    scheduled_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PostSchedule(BaseModel):
    scheduled_time: datetime
