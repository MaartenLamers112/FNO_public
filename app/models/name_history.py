"""SQLAlchemy-model voor historische naamwijzigingen."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.mixins import utc_now

if TYPE_CHECKING:
    from app.models.person import Person
    from app.models.user import User


class NameHistory(BaseModel):
    """Eén historische wijziging van de naam van een persoon."""

    __tablename__ = "name_history"

    person_id: Mapped[int] = mapped_column(
        ForeignKey("person.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    old_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    new_name: Mapped[str] = mapped_column(
        String(250),
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

    person: Mapped[Person] = relationship(
        "Person",
        back_populates="name_history",
    )

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="name_changes",
    )
