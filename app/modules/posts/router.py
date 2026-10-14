import io
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from database.session import get_db
from modules.posts.schemas import (
    PostCreate, PostResponse, PostRefine, PostSchedule,
    StyleTemplateCreate, StyleTemplateResponse
)
from modules.posts.service import PostService
from modules.posts.carousel_renderer import render_carousel_pdf
from modules.scheduler.tasks import schedule_post_job

router = APIRouter(prefix="/api")

def to_post_response(post) -> PostResponse:
    """
    Helper to convert Post model to PostResponse schema,
    converting JSON-encoded web_sources to a Python list.
    """
    web_sources_list = None
    if post.web_sources:
        try:
            web_sources_list = json.loads(post.web_sources)
        except Exception:
            web_sources_list = [post.web_sources]
            
    return PostResponse(
        id=post.id,
        title=post.title,
        type=post.type,
        rough_draft=post.rough_draft,
        web_sources=web_sources_list,
        auto_search_count=post.auto_search_count,
        style_template_id=post.style_template_id,
        content=post.content,
        status=post.status,
        scheduled_time=post.scheduled_time,
        created_at=post.created_at,
        updated_at=post.updated_at
    )

# --- Post Endpoints ---

@router.get("/posts", response_model=List[PostResponse])
def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = PostService.get_posts(db, skip=skip, limit=limit)
    return [to_post_response(p) for p in posts]

@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = PostService.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return to_post_response(post)

@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post_data: PostCreate, db: Session = Depends(get_db)):
    try:
        # Create record in DB
        post = PostService.create_post(db, post_data)
        
        # If no scheduled time, generate immediately
        if not post.scheduled_time:
            post = await PostService.generate_post_content(db, post.id)
        else:
            # Register with APScheduler background job
            schedule_post_job(post.id, post.scheduled_time)
            
        return to_post_response(post)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(ex) if 'ex' in locals() else str(e)}")

@router.post("/posts/{post_id}/refine", response_model=PostResponse)
def refine_post(post_id: int, refine_data: PostRefine, db: Session = Depends(get_db)):
    try:
        post = PostService.refine_post_content(db, post_id, refine_data.instruction)
        return to_post_response(post)
    except ValueError as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e) else 400, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {str(e)}")

@router.post("/posts/{post_id}/regenerate", response_model=PostResponse)
async def regenerate_post(post_id: int, db: Session = Depends(get_db)):
    try:
        post = await PostService.generate_post_content(db, post_id)
        return to_post_response(post)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

@router.get("/posts/{post_id}/carousel.pdf")
def download_carousel_pdf(post_id: int, db: Session = Depends(get_db)):
    post = PostService.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.type != "carousel":
        raise HTTPException(status_code=400, detail="Post is not a carousel")
    if not post.content:
        raise HTTPException(status_code=400, detail="Carousel has no generated content yet")

    try:
        slides = json.loads(post.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Carousel content is not valid JSON")

    try:
        pdf_bytes = render_carousel_pdf(slides)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"carousel_{post_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/posts/{post_id}/schedule", response_model=PostResponse)
def schedule_post(post_id: int, schedule_data: PostSchedule, db: Session = Depends(get_db)):
    post = PostService.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Update to scheduled
    post.scheduled_time = schedule_data.scheduled_time
    post.status = "scheduled"
    db.commit()
    db.refresh(post)
    
    # Schedule background job
    schedule_post_job(post.id, post.scheduled_time)
    
    return to_post_response(post)

@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    success = PostService.delete_post(db, post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Post deleted successfully"}

# --- Style Template Endpoints ---

@router.get("/style-templates", response_model=List[StyleTemplateResponse])
def get_style_templates(db: Session = Depends(get_db)):
    return PostService.get_style_templates(db)

@router.post("/style-templates", response_model=StyleTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_style_template(template_data: StyleTemplateCreate, db: Session = Depends(get_db)):
    return PostService.create_style_template(db, template_data)

@router.delete("/style-templates/{template_id}")
def delete_style_template(template_id: int, db: Session = Depends(get_db)):
    success = PostService.delete_style_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Style template not found")
    return {"detail": "Style template deleted successfully"}
