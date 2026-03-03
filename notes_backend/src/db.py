import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def _to_async_driver(url: str) -> str:
    """
    Convert common PostgreSQL URLs to an asyncpg URL usable by SQLAlchemy async engine.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        # Some platforms still use postgres://
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# PUBLIC_INTERFACE
def get_database_url() -> str:
    """Return the configured database URL.

    Environment variables expected (provided by platform/.env):
    - POSTGRES_URL (preferred; may be full DSN)
    - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT (fallback pieces)

    Returns:
        A SQLAlchemy async database URL (postgresql+asyncpg://...).
    """
    dsn = os.getenv("POSTGRES_URL")
    if dsn:
        return _to_async_driver(dsn)

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    db = os.getenv("POSTGRES_DB", "notemaster")
    port = os.getenv("POSTGRES_PORT", "5001")
    host = "localhost"  # the platform maps the db container locally for backend
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


_ENGINE: AsyncEngine | None = None
_SESSIONMAKER: async_sessionmaker[AsyncSession] | None = None


# PUBLIC_INTERFACE
def get_engine() -> AsyncEngine:
    """Return a singleton AsyncEngine instance."""
    global _ENGINE, _SESSIONMAKER
    if _ENGINE is None:
        _ENGINE = create_async_engine(
            get_database_url(),
            pool_pre_ping=True,
            future=True,
        )
        _SESSIONMAKER = async_sessionmaker(_ENGINE, expire_on_commit=False, class_=AsyncSession)
    return _ENGINE


# PUBLIC_INTERFACE
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return a singleton async sessionmaker."""
    if _SESSIONMAKER is None:
        # get_engine() initializes both _ENGINE and _SESSIONMAKER
        get_engine()
    assert _SESSIONMAKER is not None
    return _SESSIONMAKER


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency providing an AsyncSession per request."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        await session.close()
