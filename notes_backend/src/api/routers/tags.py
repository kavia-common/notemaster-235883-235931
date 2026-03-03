from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db_session
from src.repository import delete_tag, list_tags, rename_tag
from src.schemas import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    response_model=list[TagOut],
    summary="List tags",
    description="List all tags sorted alphabetically.",
    operation_id="list_tags",
)
async def list_tags_endpoint(session: AsyncSession = Depends(get_db_session)) -> list[TagOut]:
    """List tags."""
    return await list_tags(session)


@router.patch(
    "/{tag_id}",
    response_model=TagOut,
    summary="Rename tag",
    description="Rename an existing tag (name must stay unique).",
    operation_id="rename_tag",
)
async def rename_tag_endpoint(
    tag_id: int,
    name: str = Query(..., min_length=1, max_length=64, description="New unique tag name."),
    session: AsyncSession = Depends(get_db_session),
) -> TagOut:
    """Rename a tag."""
    try:
        tag = await rename_tag(session, tag_id, name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except IntegrityError as e:
        # unique constraint
        raise HTTPException(status_code=409, detail="Tag name already exists.") from e

    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found.")
    return tag


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tag",
    description="Delete a tag (removes it from all notes).",
    operation_id="delete_tag",
)
async def delete_tag_endpoint(tag_id: int, session: AsyncSession = Depends(get_db_session)) -> None:
    """Delete a tag."""
    ok = await delete_tag(session, tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tag not found.")
    return None
