from sqlalchemy.ext.asyncio import AsyncEngine

from src.models import Base


# PUBLIC_INTERFACE
async def init_db(engine: AsyncEngine) -> None:
    """Create DB tables if they don't exist.

    This keeps the project self-contained for the MVP. In production you'd use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
