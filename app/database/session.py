from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Configure SQLite specific arguments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_light_migrations():
    """
    There's no Alembic in this project, so new nullable columns on existing
    tables are added here with a plain ALTER TABLE instead of a migration framework.
    """
    inspector = inspect(engine)
    if "posts" not in inspector.get_table_names():
        return
    existing_columns = {c["name"] for c in inspector.get_columns("posts")}
    if "auto_search_count" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE posts ADD COLUMN auto_search_count INTEGER"))
