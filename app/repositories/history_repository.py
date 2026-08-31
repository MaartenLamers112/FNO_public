"""Repository voor de algemene wijzigingsgeschiedenis."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.extensions import db
from app.models import History, Photo, User
from app.models.mixins import normalize_utc
from app.repositories.base_repository import BaseRepository


class HistoryRepository(BaseRepository[History]):
    """Databasebewerkingen voor het centrale auditlog."""

    model = History

    def create(
        self,
        *,
        photo_id: int,
        event_type: str,
        description: str,
        person_id: int | None = None,
        user_id: int | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> History:
        """Maak een nieuwe geschiedenisregel aan."""

        history = History(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            event_type=event_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
        )

        return self.add(history)

    def get_by_photo(
        self,
        photo_id: int,
    ) -> list[History]:
        """Geef de historie van één foto terug, nieuwste eerst."""

        statement = (
            select(History)
            .where(History.photo_id == photo_id)
            .order_by(
                History.created_at.desc(),
                History.id.desc(),
            )
        )

        return list(db.session.scalars(statement))

    def get_by_person(
        self,
        person_id: int,
    ) -> list[History]:
        """Geef de historie van één persoon terug, nieuwste eerst."""

        statement = (
            select(History)
            .where(History.person_id == person_id)
            .order_by(
                History.created_at.desc(),
                History.id.desc(),
            )
        )

        return list(db.session.scalars(statement))

    def get_by_user(
        self,
        user_id: int,
    ) -> list[History]:
        """Geef de door een gebruiker veroorzaakte historie terug."""

        statement = (
            select(History)
            .where(History.user_id == user_id)
            .order_by(
                History.created_at.desc(),
                History.id.desc(),
            )
        )

        return list(db.session.scalars(statement))

    def get_recent(
        self,
        *,
        limit: int = 50,
    ) -> list[History]:
        """Geef de meest recente geschiedenisregels terug."""

        statement = (
            select(History)
            .order_by(
                History.created_at.desc(),
                History.id.desc(),
            )
            .limit(limit)
        )

        return list(db.session.scalars(statement))

    def get_created_between(
        self,
        *,
        started_at: datetime,
        ended_at: datetime,
    ) -> list[History]:
        """Geef historie binnen een UTC-periode terug."""

        normalized_start = normalize_utc(started_at)
        normalized_end = normalize_utc(ended_at)

        statement = (
            select(History)
            .where(
                History.created_at >= normalized_start,
                History.created_at <= normalized_end,
            )
            .order_by(
                History.created_at,
                History.id,
            )
        )

        return list(db.session.scalars(statement))

    def search(
        self,
        *,
        photo_number: str = "",
        event_type: str = "",
        username: str = "",
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> list[History]:
        """Zoek historie met beheerfilters."""

        statement = select(History).join(Photo)
        if username:
            statement = statement.outerjoin(User).where(
                User.username.ilike(f"%{username}%")
            )
        if photo_number:
            statement = statement.where(Photo.photo_number.ilike(f"%{photo_number}%"))
        if event_type:
            statement = statement.where(History.event_type == event_type)
        if started_at:
            statement = statement.where(History.created_at >= normalize_utc(started_at))
        if ended_at:
            statement = statement.where(History.created_at <= normalize_utc(ended_at))
        statement = statement.order_by(History.created_at.desc(), History.id.desc())
        return list(db.session.scalars(statement))

    def count_by_photo(
        self,
        photo_id: int,
    ) -> int:
        """Tel de geschiedenisregels van één foto."""

        statement = (
            select(func.count())
            .select_from(History)
            .where(History.photo_id == photo_id)
        )

        return db.session.scalar(statement) or 0
