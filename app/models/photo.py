"""SQLAlchemy-model voor foto's."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums.publication_status import PublicationStatus
from app.models.base import BaseModel
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.history import History
    from app.models.metadata_history import MetadataHistory
    from app.models.person import Person


class Photo(TimestampMixin, BaseModel):
    """Centrale foto-entiteit binnen FNO."""

    __tablename__ = "photo"

    mm_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    photo_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    publication_status: Mapped[int] = mapped_column(
        Integer,
        default=PublicationStatus.CONCEPT,
        nullable=False,
        index=True,
    )

    mm_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    local_subject: Mapped[str | None] = mapped_column(String(250), nullable=True)

    local_date: Mapped[str | None] = mapped_column(String(100), nullable=True)

    local_location: Mapped[str | None] = mapped_column(String(250), nullable=True)

    local_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    is_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    person_display_mode: Mapped[str] = mapped_column(
        String(20),
        default="numbered",
        nullable=False,
    )

    label_size: Mapped[int] = mapped_column(
        Integer,
        default=14,
        nullable=False,
    )

    person_display_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    synchronized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    persons: Mapped[list[Person]] = relationship(
        "Person",
        back_populates="photo",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="photo",
        cascade="all, delete-orphan",
    )

    metadata_history: Mapped[list[MetadataHistory]] = relationship(
        "MetadataHistory",
        back_populates="photo",
        cascade="all, delete-orphan",
        order_by="MetadataHistory.changed_at",
    )

    history: Mapped[list[History]] = relationship(
        "History",
        back_populates="photo",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        """Geef het fotonummer terug."""

        return self.photo_number
