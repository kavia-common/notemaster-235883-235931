from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TagOut(BaseModel):
    id: int = Field(..., description="Tag ID.")
    name: str = Field(..., description="Unique tag name.")

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    title: str = Field("", max_length=200, description="Note title.")
    content: str = Field("", description="Markdown content.")


class NoteCreate(NoteBase):
    tag_names: List[str] = Field(default_factory=list, description="Optional list of tag names to set on creation.")
    pinned: bool = Field(default=False, description="Whether the note is pinned.")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="New note title.")
    content: Optional[str] = Field(None, description="New markdown content.")
    tag_names: Optional[List[str]] = Field(None, description="If provided, replaces tags with these names.")
    pinned: Optional[bool] = Field(None, description="If provided, sets pinned state.")


class NoteAutosave(BaseModel):
    title: Optional[str] = Field(None, max_length=200, description="Autosaved note title.")
    content: Optional[str] = Field(None, description="Autosaved note content.")
    tag_names: Optional[List[str]] = Field(None, description="Optional replacement tags.")
    # autosave intentionally doesn't allow pin toggle to avoid accidental changes


class NoteOut(BaseModel):
    id: int = Field(..., description="Note ID.")
    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Markdown content.")
    pinned: bool = Field(..., description="Pinned flag.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC).")
    tags: List[TagOut] = Field(default_factory=list, description="Tags assigned to the note.")

    class Config:
        from_attributes = True


class NotesListOut(BaseModel):
    items: List[NoteOut] = Field(..., description="Notes list.")
    total: int = Field(..., description="Total matching notes count.")
