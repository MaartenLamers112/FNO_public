"""SQLAlchemy-model voor historische metadatawijzigingen."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.photo import Photo
    from app.models.user import User


class MetadataHistory(BaseModel):
    """Eén historische wijziging van een metadataveld van een foto."""

    __tablename__ = "metadata_history"

    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photo.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    old_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    new_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    photo: Mapped[Photo] = relationship(
        "Photo",
        back_populates="metadata_history",
    )

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="metadata_changes",
    )
