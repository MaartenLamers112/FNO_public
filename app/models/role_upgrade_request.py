"""SQLAlchemy-model voor aanvragen om een hogere gebruikersrol."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class RoleUpgradeRequest(BaseModel):
    """Persistente aanvraag voor een hogere gebruikersrol."""

    __tablename__ = "role_upgrade_request"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    requested_role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="role_upgrade_requests",
    )
    reviewed_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
        back_populates="reviewed_role_upgrade_requests",
    )
