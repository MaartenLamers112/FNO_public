"""API-schema's voor opmerkingen."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.enums.author_type import AuthorType
from app.enums.comment_status import CommentStatus


class CommentCreate(BaseModel):
    """Nieuwe opmerking."""

    content: str


class CommentUpdate(BaseModel):
    """Gewijzigde opmerking."""

    content: str


class PersonCommentTextUpdate(BaseModel):
    """Doorlopende opmerkingstekst van een persoon."""

    content: str


class PersonCommentTextResponse(BaseModel):
    """Samengevoegde opmerkingstekst van een persoon."""

    person_id: int
    content: str
    has_comment: bool


class CommentResponse(BaseModel):
    """Representatie van een opmerking."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_id: int
    person_id: int | None
    content: str
    author_type: AuthorType
    status: CommentStatus
    created_at: datetime

    @field_serializer("author_type")
    def serialize_author_type(self, value: AuthorType) -> str:
        """Serialiseer het auteurstype."""

        return value.name.lower()

    @field_serializer("status")
    def serialize_status(self, value: CommentStatus) -> str:
        """Serialiseer de status."""

        return value.name.lower()
