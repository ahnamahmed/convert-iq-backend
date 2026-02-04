from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()


# --------------------------------------------------
# SQLAlchemy Engine
# --------------------------------------------------
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,  # avoids stale Supabase connections
)


# --------------------------------------------------
# Session
# --------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# --------------------------------------------------
# Base (USED BY ALEMBIC)
# --------------------------------------------------
class Base(DeclarativeBase):
    pass


# --------------------------------------------------
# Dependency (FastAPI)
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()