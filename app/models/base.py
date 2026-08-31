"""Gemeenschappelijke basisklasse voor SQLAlchemy-modellen."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class BaseModel(db.Model):
    """Abstracte basis met een interne integer-primary-key."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    def __repr__(self) -> str:
        """Geef een compacte technische modelrepresentatie terug."""

        return f"<{self.__class__.__name__} id={self.id}>"

    def to_dict(self) -> dict[str, Any]:
        """Converteer alle databasekolommen naar een dictionary."""

        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }
