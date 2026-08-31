"""Herbruikbare kolommixins en datumhelpers voor SQLAlchemy-modellen."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Geef de huidige UTC-tijd terug zonder tijdzone-informatie.

    SQLite bewaart geen tijdzone-offset. Binnen FNO worden alle naïeve
    datetimes daarom consequent als UTC geïnterpreteerd.
    """

    return datetime.now(UTC).replace(tzinfo=None)


def normalize_utc(value: datetime) -> datetime:
    """Converteer een datetime naar naïeve UTC voor databaseopslag."""

    if value.tzinfo is None:
        return value

    return value.astimezone(UTC).replace(tzinfo=None)


class CreatedAtMixin:
    """Voeg uitsluitend een aanmaakdatum toe."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    """Voeg een aanmaakdatum en wijzigingsdatum toe."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
