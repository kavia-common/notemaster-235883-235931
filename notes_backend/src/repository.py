from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Note, Tag, note_tags


async def _get_or_create_tags(session: AsyncSession, tag_names: Iterable[str]) -> List[Tag]:
    names = sorted({n.strip() for n in tag_names if n and n.strip()})
    if not names:
        return []

    existing = (
        await session.execute(select(Tag).where(Tag.name.in_(names)))
    ).scalars().all()
    existing_map = {t.name: t for t in existing}

    tags: List[Tag] = []
    for n in names:
        tag = existing_map.get(n)
        if tag is None:
            tag = Tag(name=n)
            session.add(tag)
            tags.append(tag)
        else:
            tags.append(tag)

    # Flush to ensure new tags get IDs before association.
    await session.flush()
    return tags


def _note_with_relations_stmt() -> Select:
    return select(Note).options(selectinload(Note.tags))


# PUBLIC_INTERFACE
async def create_note(
    session: AsyncSession,
    title: str,
    content: str,
    tag_names: Iterable[str],
    pinned: bool,
) -> Note:
    """Create a note and optionally assign tags."""
    note = Note(title=title or "", content=content or "", pinned=bool(pinned))
    session.add(note)
    await session.flush()  # get note.id

    tags = await _get_or_create_tags(session, tag_names)
    note.tags = tags
    await session.commit()
    await session.refresh(note)
    return note


# PUBLIC_INTERFACE
async def get_note(session: AsyncSession, note_id: int) -> Optional[Note]:
    """Fetch one note by id."""
    res = await session.execute(_note_with_relations_stmt().where(Note.id == note_id))
    return res.scalars().first()


# PUBLIC_INTERFACE
async def update_note(
    session: AsyncSession,
    note: Note,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tag_names: Optional[Iterable[str]] = None,
    pinned: Optional[bool] = None,
) -> Note:
    """Update a note (partial update)."""
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if pinned is not None:
        note.pinned = bool(pinned)

    if tag_names is not None:
        tags = await _get_or_create_tags(session, tag_names)
        note.tags = tags

    await session.commit()
    await session.refresh(note)
    return note


# PUBLIC_INTERFACE
async def delete_note(session: AsyncSession, note_id: int) -> bool:
    """Delete note by id. Returns True if deleted."""
    res = await session.execute(delete(Note).where(Note.id == note_id).returning(Note.id))
    deleted = res.scalar_one_or_none()
    await session.commit()
    return deleted is not None


# PUBLIC_INTERFACE
async def list_notes(
    session: AsyncSession,
    *,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    pinned: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Note], int]:
    """List notes with optional search/tag/pinned filters."""
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    stmt = _note_with_relations_stmt()
    count_stmt = select(func.count(Note.id))

    where_clauses = []

    if q:
        like = f"%{q.strip()}%"
        where_clauses.append(or_(Note.title.ilike(like), Note.content.ilike(like)))

    if pinned is not None:
        where_clauses.append(Note.pinned.is_(bool(pinned)))

    if tag:
        # Join through association
        stmt = stmt.join(note_tags).join(Tag).where(Tag.name == tag)
        count_stmt = count_stmt.join(note_tags).join(Tag).where(Tag.name == tag)

    if where_clauses:
        stmt = stmt.where(and_(*where_clauses))
        count_stmt = count_stmt.where(and_(*where_clauses))

    stmt = stmt.order_by(Note.pinned.desc(), Note.updated_at.desc()).limit(limit).offset(offset)

    items = (await session.execute(stmt)).scalars().unique().all()
    total = (await session.execute(count_stmt)).scalar_one()
    return items, int(total)


# PUBLIC_INTERFACE
async def set_pinned(session: AsyncSession, note: Note, pinned: bool) -> Note:
    """Pin/unpin a note."""
    note.pinned = bool(pinned)
    await session.commit()
    await session.refresh(note)
    return note


# PUBLIC_INTERFACE
async def list_tags(session: AsyncSession) -> List[Tag]:
    """List tags."""
    stmt = select(Tag).order_by(Tag.name.asc())
    return (await session.execute(stmt)).scalars().all()


# PUBLIC_INTERFACE
async def rename_tag(session: AsyncSession, tag_id: int, new_name: str) -> Optional[Tag]:
    """Rename a tag; returns updated tag or None if not found."""
    new_name = (new_name or "").strip()
    if not new_name:
        raise ValueError("Tag name cannot be empty.")

    tag = (await session.execute(select(Tag).where(Tag.id == tag_id))).scalars().first()
    if tag is None:
        return None

    tag.name = new_name
    await session.commit()
    await session.refresh(tag)
    return tag


# PUBLIC_INTERFACE
async def delete_tag(session: AsyncSession, tag_id: int) -> bool:
    """Delete a tag and associations."""
    res = await session.execute(delete(Tag).where(Tag.id == tag_id).returning(Tag.id))
    deleted = res.scalar_one_or_none()
    await session.commit()
    return deleted is not None
