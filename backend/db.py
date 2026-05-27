"""Database initialization and session helpers using SQLAlchemy (SQLite).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings


DATABASE_URL = settings.database_url

# SQLite needs check_same_thread disabled for multithreading in FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create database tables."""
    from models.db_models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)
