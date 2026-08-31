"""
SQLAlchemy-model voor gebruikersrollen.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Role(BaseModel):
    """Gebruikersrol binnen FNO."""

    __tablename__ = "role"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    users = relationship(
        "User",
        back_populates="role",
    )
