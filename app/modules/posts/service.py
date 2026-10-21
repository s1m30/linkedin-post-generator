import json
import re
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from modules.posts.models import Post, StyleTemplate
from modules.posts.schemas import PostCreate, PostUpdate, StyleTemplateCreate
from modules.posts.web_search import search_web
from modules.ai.engine import ai_engine
from modules.ai import prompts

async def scrape_url(url: str) -> str:
    """
    Fetches the webpage content, strips HTML tags, and returns the cleaned text.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            }
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return f"[Error fetching URL {url}: HTTP {response.status_code}]"
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove scripts, styles, and heavy navigation elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            # Extract plain text
            text = soup.get_text(separator="\n")
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = "\n".join(chunk for chunk in chunks if chunk)
            
            # Keep it reasonable to fit in context window
            return f"--- Content from {url} ---\n{text_content[:4000]}\n"
    except Exception as e:
        return f"[Error scraping URL {url}: {str(e)}]"

def clean_json_content(content: str) -> str:
    """
    Cleans up potential markdown wrapper (e.g. ```json ... ```) from LLM response.
    """
    content = content.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", content, re.DOTALL)
    if match:
        content = match.group(1).strip()
    return content

class PostService:
    @staticmethod
    def get_post(db: Session, post_id: int, user_id: UUID) -> Optional[Post]:
        return db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()

    @staticmethod
    def get_posts(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Post]:
        return (
            db.query(Post)
            .filter(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create_post(db: Session, post_data: PostCreate, user_id: UUID) -> Post:
        web_sources_str = json.dumps(post_data.web_sources) if post_data.web_sources else None
        style_template_id = post_data.style_template_id
        if style_template_id is not None:
            # Don't let a post reference another user's style template.
            owned = db.query(StyleTemplate).filter(
                StyleTemplate.id == style_template_id, StyleTemplate.user_id == user_id
            ).first()
            if not owned:
                style_template_id = None

        db_post = Post(
            user_id=user_id,
            title=post_data.title,
            type=post_data.type,
            mode=post_data.mode,
            rough_draft=post_data.rough_draft,
            additional_context=post_data.additional_context,
            web_sources=web_sources_str,
            auto_search_count=post_data.auto_search_count,
            style_template_id=style_template_id,
            status="scheduled" if post_data.scheduled_time else "draft",
            scheduled_time=post_data.scheduled_time
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def update_post(db: Session, post_id: int, user_id: UUID, update_data: PostUpdate) -> Optional[Post]:
        """
        Patches an existing draft's editable fields (used by Assist mode to save
        iterative edits, but applies to any post).
        """
        db_post = PostService.get_post(db, post_id, user_id)
        if not db_post:
            return None

        fields = update_data.model_dump(exclude_unset=True)
        if "web_sources" in fields:
            fields["web_sources"] = json.dumps(fields["web_sources"]) if fields["web_sources"] else None
        if fields.get("style_template_id") is not None:
            owned = db.query(StyleTemplate).filter(
                StyleTemplate.id == fields["style_template_id"], StyleTemplate.user_id == user_id
            ).first()
            if not owned:
                fields["style_template_id"] = None
        for key, value in fields.items():
            setattr(db_post, key, value)

        db_post.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def update_post_status(db: Session, post_id: int, user_id: UUID, status: str) -> Optional[Post]:
        db_post = PostService.get_post(db, post_id, user_id)
        if db_post:
            db_post.status = status
            db_post.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_post)
        return db_post

    @staticmethod
    def delete_post(db: Session, post_id: int, user_id: UUID) -> bool:
        db_post = PostService.get_post(db, post_id, user_id)
        if db_post:
            db.delete(db_post)
            db.commit()
            return True
        return False

    @staticmethod
    async def _resolve_web_context(db: Session, db_post: Post) -> str:
        """
        Resolves manually provided + auto-searched web sources into scraped text.
        Persists the combined URL list back onto the post so auto-fetched sources
        remain visible and checkable after generation, not just used and discarded.
        """
        manual_urls = json.loads(db_post.web_sources) if db_post.web_sources else []
        manual_urls = [u.strip() for u in manual_urls if u.strip()]

        search_urls = []
        if db_post.auto_search_count:
            query = (db_post.title or db_post.rough_draft or "").strip()
            if query:
                search_urls = search_web(query, max_results=db_post.auto_search_count)
                search_urls = [u for u in search_urls if u not in manual_urls]

        all_urls = manual_urls + search_urls
        scraped_texts = [await scrape_url(url) for url in all_urls]

        if search_urls:
            db_post.web_sources = json.dumps(all_urls)

        return "\n".join(scraped_texts)

    @staticmethod
    def _get_style_content(db: Session, db_post: Post) -> str:
        if db_post.style_template_id:
            template = db.query(StyleTemplate).filter(
                StyleTemplate.id == db_post.style_template_id, StyleTemplate.user_id == db_post.user_id
            ).first()
            if template:
                return template.content
        return ""

    @staticmethod
    async def generate_post_content(db: Session, post_id: int, user_id: UUID) -> Post:
        """
        Gathers context (rough drafts, scraping URLs, style templates) and calls the AI engine.
        Updates the post content and status.
        """
        db_post = PostService.get_post(db, post_id, user_id)
        if not db_post:
            raise ValueError(f"Post {post_id} not found")

        web_content = await PostService._resolve_web_context(db, db_post)
        style_content = PostService._get_style_content(db, db_post)

        # Generating prompt & calling LLM based on type
        if db_post.type == "carousel":
            # For carousels we default to a structured output, say 5 slides if not specified.
            # We can parse the rough draft for slide requests if any.
            num_slides = 5
            # Basic parsing to see if user wants a specific number of slides:
            match = re.search(r"(\d+)\s*slides", (db_post.rough_draft or ""), re.IGNORECASE)
            if match:
                num_slides = int(match.group(1))

            system_prompt = prompts.CAROUSEL_SYSTEM_PROMPT
            user_prompt = prompts.build_carousel_user_prompt(
                title=db_post.title,
                num_slides=num_slides,
                rough_draft=db_post.rough_draft,
                additional_context=db_post.additional_context,
                web_sources_text=web_content,
                style_template_content=style_content
            )
            raw_content = ai_engine.generate(system_prompt, user_prompt)
            content = clean_json_content(raw_content)
        else:
            # Regular text post
            system_prompt = prompts.POST_SYSTEM_PROMPT
            user_prompt = prompts.build_post_user_prompt(
                title=db_post.title,
                rough_draft=db_post.rough_draft,
                additional_context=db_post.additional_context,
                web_sources_text=web_content,
                style_template_content=style_content
            )
            content = ai_engine.generate(system_prompt, user_prompt)

        # Update database record
        db_post.content = content
        # If it was scheduled and just finished generating, it is now "completed"
        if db_post.status == "scheduled":
            db_post.status = "completed"
        db_post.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    def refine_post_content(db: Session, post_id: int, user_id: UUID, instruction: str) -> Post:
        """
        Refines already generated content based on feedback.
        """
        db_post = PostService.get_post(db, post_id, user_id)
        if not db_post:
            raise ValueError(f"Post {post_id} not found")
        if not db_post.content:
            raise ValueError(f"Post {post_id} has no generated content to refine")

        style_content = PostService._get_style_content(db, db_post)

        # Reconstruct the original request context for LLM memory
        original_prompt = f"Topic/Title: {db_post.title or 'N/A'}\nRough Draft: {db_post.rough_draft or 'N/A'}"
        if style_content:
            original_prompt += f"\nStyle template used:\n{style_content}"

        if db_post.type == "carousel":
            system_prompt = prompts.REFINEMENT_CAROUSEL_SYSTEM_PROMPT
            raw_content = ai_engine.refine(system_prompt, original_prompt, db_post.content, instruction)
            content = clean_json_content(raw_content)
        else:
            system_prompt = prompts.REFINEMENT_POST_SYSTEM_PROMPT
            content = ai_engine.refine(system_prompt, original_prompt, db_post.content, instruction)

        db_post.content = content
        db_post.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_post)
        return db_post

    @staticmethod
    async def assist_post(db: Session, post_id: int, user_id: UUID) -> Post:
        """
        Non-destructive editorial pass: fact-checks and suggests structure for the
        user's own rough draft without ever overwriting it. Re-runnable as the
        draft evolves; each run simply replaces the previous advisory result.
        """
        db_post = PostService.get_post(db, post_id, user_id)
        if not db_post:
            raise ValueError(f"Post {post_id} not found")

        web_content = await PostService._resolve_web_context(db, db_post)
        style_content = PostService._get_style_content(db, db_post)

        user_prompt = prompts.build_assist_user_prompt(
            title=db_post.title,
            rough_draft=db_post.rough_draft,
            additional_context=db_post.additional_context,
            web_sources_text=web_content,
            style_template_content=style_content
        )
        raw_result = ai_engine.generate(prompts.ASSIST_SYSTEM_PROMPT, user_prompt)
        db_post.assist_result = clean_json_content(raw_result)
        db_post.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_post)
        return db_post

    # Style Templates CRUD
    @staticmethod
    def get_style_templates(db: Session, user_id: UUID) -> List[StyleTemplate]:
        return db.query(StyleTemplate).filter(StyleTemplate.user_id == user_id).order_by(StyleTemplate.name).all()

    @staticmethod
    def create_style_template(db: Session, template_data: StyleTemplateCreate, user_id: UUID) -> StyleTemplate:
        db_template = StyleTemplate(
            user_id=user_id,
            name=template_data.name,
            content=template_data.content
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def delete_style_template(db: Session, template_id: int, user_id: UUID) -> bool:
        db_template = db.query(StyleTemplate).filter(
            StyleTemplate.id == template_id, StyleTemplate.user_id == user_id
        ).first()
        if db_template:
            db.delete(db_template)
            db.commit()
            return True
        return False
