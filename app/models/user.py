"""SQLAlchemy-model voor geauthenticeerde FNO-gebruikers."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.base import BaseModel
from app.models.mixins import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.history import History
    from app.models.metadata_history import MetadataHistory
    from app.models.name_history import NameHistory
    from app.models.role import Role
    from app.models.setting import Setting


class User(UserMixin, CreatedAtMixin, BaseModel):
    """Ingelogde FNO-gebruiker met een rol."""

    __tablename__ = "user"

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        unique=True,
        nullable=True,
        index=True,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("role.id"),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    role: Mapped[Role] = relationship(
        "Role",
        back_populates="users",
    )

    history: Mapped[list[History]] = relationship(
        "History",
        back_populates="user",
        passive_deletes=True,
    )

    name_changes: Mapped[list[NameHistory]] = relationship(
        "NameHistory",
        back_populates="user",
        passive_deletes=True,
    )

    metadata_changes: Mapped[list[MetadataHistory]] = relationship(
        "MetadataHistory",
        back_populates="user",
        passive_deletes=True,
    )

    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        foreign_keys="Comment.user_id",
        back_populates="author",
    )

    closed_comments: Mapped[list[Comment]] = relationship(
        "Comment",
        foreign_keys="Comment.closed_by_user_id",
        back_populates="closed_by_user",
    )

    deleted_comments: Mapped[list[Comment]] = relationship(
        "Comment",
        foreign_keys="Comment.deleted_by_user_id",
        back_populates="deleted_by_user",
    )

    updated_settings: Mapped[list[Setting]] = relationship(
        "Setting",
        back_populates="updated_by_user",
    )

    def set_password(self, password: str) -> None:
        """Hash en bewaar een nieuw wachtwoord."""

        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
        )

    def check_password(self, password: str) -> bool:
        """Controleer een wachtwoord tegen de opgeslagen hash."""

        return check_password_hash(
            self.password_hash,
            password,
        )

    def get_id(self) -> str:
        """Geef de gebruikers-ID terug voor Flask-Login."""

        return str(self.id)
