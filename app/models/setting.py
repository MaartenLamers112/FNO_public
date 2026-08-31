"""SQLAlchemy-model voor functionele applicatie-instellingen."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class Setting(BaseModel):
    """Configureerbare functionele instelling binnen FNO."""

    __tablename__ = "setting"

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    updated_by_user: Mapped[User | None] = relationship(
        "User",
        back_populates="updated_settings",
    )

    def __str__(self) -> str:
        """Geef de sleutel terug als leesbare representatie."""

        return self.key
