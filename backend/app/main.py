from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .api import api_router
from .config import STORAGE_STATE_FILE, DATABASE_FILE

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    init_db()
    yield

app = FastAPI(
    title="Study Pilot API",
    description="Local Academic Workflow Assistant & Moodle Monitor",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for local Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Study Pilot API",
        "database_connected": DATABASE_FILE.exists(),
        "is_authenticated": STORAGE_STATE_FILE.exists()
    }

# Mount all API routes
app.include_router(api_router)
