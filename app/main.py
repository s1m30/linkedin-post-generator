import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure the backend directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.session import Base, engine, run_light_migrations
from modules.posts.router import router as api_router
from modules.scheduler.tasks import scheduler, load_scheduled_posts

# Initialize Database tables
Base.metadata.create_all(bind=engine)
run_light_migrations()

app = FastAPI(
    title="LinkedIn Post & Carousel Generator",
    description="Local tool to generate, schedule, and refine LinkedIn content",
    version="1.0.0"
)

# Enable CORS for local cross-origin requests if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dynamic path resolution for static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

# Ensure static folder exists
os.makedirs(static_dir, exist_ok=True)

# Register API Router
app.include_router(api_router)

# Mount Static Files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def get_index():
    """
    Serve the main index.html for the frontend SPA.
    """
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend index.html not found. Please verify Phase 6 UI files."}

# Startup and Shutdown events
@app.on_event("startup")
def startup_event():
    # Start APScheduler
    scheduler.start()
    # Load previously scheduled posts from database
    load_scheduled_posts()

@app.on_event("shutdown")
def shutdown_event():
    # Shutdown APScheduler
    scheduler.shutdown()
