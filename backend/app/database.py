from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_URL, DATABASE_FILE

# SQLite specific connect args for thread safety with FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    """Initialize SQLite database tables."""
    # Ensure parent directory exists
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    with Session(engine, expire_on_commit=False) as session:
        yield session
