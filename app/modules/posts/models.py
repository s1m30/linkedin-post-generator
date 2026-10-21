from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from database.session import Base

class StyleTemplate(Base):
    __tablename__ = "style_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Uuid, ForeignKey("profiles.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="style_template")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Uuid, ForeignKey("profiles.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    type = Column(String, nullable=False, default="post")  # "post" or "carousel"
    mode = Column(String, nullable=False, default="generate")  # "generate" (AI writes it) or "assist" (AI advises, user writes it)
    rough_draft = Column(Text, nullable=True)
    additional_context = Column(Text, nullable=True)  # Free-form user-supplied notes/context not fetched from the web
    web_sources = Column(Text, nullable=True)  # JSON-encoded array of strings (URLs)
    auto_search_count = Column(Integer, nullable=True)  # If set, fetch this many sources via web search at generation time
    style_template_id = Column(Integer, ForeignKey("style_templates.id"), nullable=True)
    content = Column(Text, nullable=True)  # Markdown string (for post) or JSON list of slides (for carousel)
    assist_result = Column(Text, nullable=True)  # JSON-encoded AssistResult (fact_check, structured_draft, suggestions, template)
    status = Column(String, nullable=False, default="draft")  # "draft", "scheduled", "completed"
    scheduled_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    style_template = relationship("StyleTemplate", back_populates="posts")
