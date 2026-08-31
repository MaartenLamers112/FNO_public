"""SQLAlchemy-model voor de algemene wijzigingsgeschiedenis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.photo import Photo
    from app.models.user import User


class History(CreatedAtMixin, BaseModel):
    """Onwijzigbare registratie van een gebeurtenis binnen FNO."""

    __tablename__ = "history"

    __table_args__ = (
        Index(
            "ix_history_photo_created_at",
            "photo_id",
            "created_at",
        ),
    )

    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photo.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    person_id: Mapped[int | None] = mapped_column(
        ForeignKey("person.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    old_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    new_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    photo: Mapped[Photo] = relationship(
        "Photo",
        back_populates="history",
    )

    person: Mapped[Person | None] = relationship(
        "Person",
        back_populates="history",
    )

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="history",
    )
