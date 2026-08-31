"""SQLAlchemy-model voor een gelabelde persoon op een foto."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.history import History
    from app.models.name_history import NameHistory
    from app.models.photo import Photo


class Person(TimestampMixin, BaseModel):
    """Persoon die voorkomt op één specifieke foto."""

    __tablename__ = "person"

    __table_args__ = (
        UniqueConstraint(
            "photo_id",
            "label_number",
            name="uq_person_photo_label",
        ),
    )

    photo_id: Mapped[int] = mapped_column(
        ForeignKey("photo.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    x_position: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    y_position: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    current_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
        index=True,
    )

    name_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    photo: Mapped[Photo] = relationship(
        "Photo",
        back_populates="persons",
    )

    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="person",
    )

    history: Mapped[list[History]] = relationship(
        "History",
        back_populates="person",
    )

    name_history: Mapped[list[NameHistory]] = relationship(
        "NameHistory",
        back_populates="person",
        cascade="all, delete-orphan",
        order_by="NameHistory.changed_at",
    )

    def __str__(self) -> str:
        """Geef de naam of het labelnummer terug."""

        return self.current_name or f"Persoon {self.label_number}"
