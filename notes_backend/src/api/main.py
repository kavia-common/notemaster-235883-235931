from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db import get_engine
from src.init_db import init_db
from src.api.routers.notes import router as notes_router
from src.api.routers.tags import router as tags_router

openapi_tags = [
    {"name": "health", "description": "Health and diagnostics endpoints."},
    {"name": "notes", "description": "Notes CRUD, search, pin/unpin, autosave."},
    {"name": "tags", "description": "Tag listing and management."},
]


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

# CORS: allow frontend to call the API. Keep permissive for MVP; can be tightened via env later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
