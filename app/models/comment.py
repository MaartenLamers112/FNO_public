"""SQLAlchemy-model voor opmerkingen bij foto's en personen."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums.author_type import AuthorType
from app.enums.comment_status import CommentStatus
from app.models.base import BaseModel
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.photo import Photo
    from app.models.user import User


class Comment(TimestampMixin, BaseModel):
    """Opmerking bij een foto of een persoon op een foto."""

    __tablename__ = "comment"

    __table_args__ = (
        Index(
            "ix_comment_photo_status",
            "photo_id",
            "status",
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
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    author_type: Mapped[str] = mapped_column(
        String(30),
        default=AuthorType.VISITOR,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=CommentStatus.OPEN,
        nullable=False,
        index=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )

    photo: Mapped[Photo] = relationship(
        "Photo",
        back_populates="comments",
    )

    person: Mapped[Person | None] = relationship(
        "Person",
        back_populates="comments",
    )

    author: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="comments",
    )

    closed_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[closed_by_user_id],
        back_populates="closed_comments",
    )

    deleted_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[deleted_by_user_id],
        back_populates="deleted_comments",
    )
