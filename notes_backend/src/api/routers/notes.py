from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db_session
from src.repository import create_note, delete_note, get_note, list_notes, set_pinned, update_note
from src.schemas import NoteAutosave, NoteCreate, NoteOut, NotesListOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get(
    "",
    response_model=NotesListOut,
    summary="List notes",
    description="List notes with optional full-text-ish search and tag filter. Sorted by pinned desc then updated_at desc.",
    operation_id="list_notes",
)
async def list_notes_endpoint(
    q: Optional[str] = Query(None, description="Search query applied to title and content."),
    tag: Optional[str] = Query(None, description="Filter by a single tag name."),
    pinned: Optional[bool] = Query(None, description="Filter by pinned state."),
    limit: int = Query(50, ge=1, le=200, description="Page size (max 200)."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    session: AsyncSession = Depends(get_db_session),
) -> NotesListOut:
    """Return a paginated list of notes."""
    items, total = await list_notes(session, q=q, tag=tag, pinned=pinned, limit=limit, offset=offset)
    return NotesListOut(items=items, total=total)


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a note with optional tags and pinned flag.",
    operation_id="create_note",
)
async def create_note_endpoint(payload: NoteCreate, session: AsyncSession = Depends(get_db_session)) -> NoteOut:
    """Create a note."""
    note = await create_note(
        session,
        title=payload.title,
        content=payload.content,
        tag_names=payload.tag_names,
        pinned=payload.pinned,
    )
    return note


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get note",
    description="Get a single note by id.",
    operation_id="get_note",
)
async def get_note_endpoint(note_id: int, session: AsyncSession = Depends(get_db_session)) -> NoteOut:
    """Fetch a note."""
    note = await get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return note


@router.patch(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update note",
    description="Partially update a note. If tag_names is provided it replaces all tags.",
    operation_id="update_note",
)
async def update_note_endpoint(
    note_id: int,
    payload: NoteUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> NoteOut:
    """Update a note (partial)."""
    note = await get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")

    note = await update_note(
        session,
        note,
        title=payload.title,
        content=payload.content,
        tag_names=payload.tag_names,
        pinned=payload.pinned,
    )
    return note


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note by id.",
    operation_id="delete_note",
)
async def delete_note_endpoint(note_id: int, session: AsyncSession = Depends(get_db_session)) -> None:
    """Delete a note."""
    ok = await delete_note(session, note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found.")
    return None


@router.post(
    "/{note_id}/pin",
    response_model=NoteOut,
    summary="Pin a note",
    description="Set pinned=true for a note.",
    operation_id="pin_note",
)
async def pin_note_endpoint(note_id: int, session: AsyncSession = Depends(get_db_session)) -> NoteOut:
    """Pin a note."""
    note = await get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return await set_pinned(session, note, True)


@router.post(
    "/{note_id}/unpin",
    response_model=NoteOut,
    summary="Unpin a note",
    description="Set pinned=false for a note.",
    operation_id="unpin_note",
)
async def unpin_note_endpoint(note_id: int, session: AsyncSession = Depends(get_db_session)) -> NoteOut:
    """Unpin a note."""
    note = await get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return await set_pinned(session, note, False)


@router.post(
    "/{note_id}/autosave",
    response_model=NoteOut,
    summary="Autosave note",
    description="Autosave endpoint to update content/title/tags without toggling pin state. Intended for frequent calls.",
    operation_id="autosave_note",
)
async def autosave_note_endpoint(
    note_id: int,
    payload: NoteAutosave,
    session: AsyncSession = Depends(get_db_session),
) -> NoteOut:
    """Autosave changes to a note."""
    note = await get_note(session, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found.")

    note = await update_note(
        session,
        note,
        title=payload.title,
        content=payload.content,
        tag_names=payload.tag_names,
        pinned=None,
    )
    return note
