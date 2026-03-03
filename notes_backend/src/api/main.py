import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.notes import router as notes_router
from src.api.routers.tags import router as tags_router
from src.db import get_engine
from src.init_db import init_db

openapi_tags = [
    {"name": "health", "description": "Health and diagnostics endpoints."},
    {"name": "notes", "description": "Notes CRUD, search, pin/unpin, autosave."},
    {"name": "tags", "description": "Tag listing and management."},
]


def _cors_origins_from_env() -> list[str]:
    """
    Build allow_origins list from env.

    Supported env vars:
    - CORS_ALLOW_ORIGINS: comma-separated list (e.g. "http://localhost:3000,https://example.com")
    - FRONTEND_URL: convenience single origin

    If neither is set, fall back to ["*"] for preview/MVP.
    """
    raw = (os.getenv("CORS_ALLOW_ORIGINS") or "").strip()
    frontend = (os.getenv("FRONTEND_URL") or "").strip()

    origins: list[str] = []
    if raw:
        origins.extend([o.strip() for o in raw.split(",") if o and o.strip()])
    if frontend:
        origins.append(frontend)

    # De-dupe while preserving order
    seen: set[str] = set()
    uniq = []
    for o in origins:
        if o not in seen:
            seen.add(o)
            uniq.append(o)

    return uniq if uniq else ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize resources on startup.

    - Creates DB tables (MVP convenience).
    """
    engine = get_engine()
    await init_db(engine)
    yield


app = FastAPI(
    title="NoteMaster Backend API",
    description="REST API for NoteMaster notes, tags, search, pinning, and autosave.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
)

# CORS: allow frontend to call the API.
# For preview/MVP this defaults to "*", but can be tightened by setting CORS_ALLOW_ORIGINS / FRONTEND_URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    tags=["health"],
    summary="Health check",
    description="Simple health check endpoint.",
    operation_id="health_check",
)
def health_check():
    """Return a basic health response."""
    return {"message": "Healthy"}


app.include_router(notes_router)
app.include_router(tags_router)
