from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from .config import DATABASE_URL, DATABASE_FILE

# SQLite specific connect args for thread safety with FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def init_db() -> None:
    """Initialize SQLite database tables and apply backward-compatible column migrations."""
    # Ensure parent directory exists
    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    
    # Backward-compatible migrations for existing SQLite databases
    with engine.connect() as conn:
        try:
            # Check moodle_activity columns
            cursor = conn.exec_driver_sql("PRAGMA table_info(moodle_activity)")
            columns = [row[1] for row in cursor.fetchall()]
            if columns:
                if "workspace_path" not in columns:
                    conn.exec_driver_sql("ALTER TABLE moodle_activity ADD COLUMN workspace_path TEXT")
                if "workspace_status" not in columns:
                    conn.exec_driver_sql("ALTER TABLE moodle_activity ADD COLUMN workspace_status TEXT DEFAULT 'uninitialized'")
                conn.commit()
        except Exception:
            pass

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    with Session(engine, expire_on_commit=False) as session:
        yield session
