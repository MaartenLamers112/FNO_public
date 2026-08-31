"""
Repository voor foto's.
"""

from __future__ import annotations

from sqlalchemy import func, select

from app.enums.publication_status import PublicationStatus
from app.extensions import db
from app.models import Photo
from app.repositories.base_repository import BaseRepository


class PhotoRepository(BaseRepository[Photo]):
    """Databasebewerkingen voor foto's."""

    model = Photo

    def get_by_mm_id(self, mm_id: str) -> Photo | None:
        """Zoek een foto op MM-id."""

        statement = select(Photo).where(Photo.mm_id == mm_id)

        return db.session.scalar(statement)

    def get_by_mm_ids(self, mm_ids: set[str]) -> list[Photo]:
        """Geef alle foto's waarvan het MM-id in de opgegeven set staat."""

        if not mm_ids:
            return []

        statement = select(Photo).where(Photo.mm_id.in_(mm_ids))
        return list(db.session.scalars(statement))

    def get_by_photo_number(
        self,
        photo_number: str,
    ) -> Photo | None:
        """Zoek een foto op fotonummer."""

        statement = select(Photo).where(Photo.photo_number == photo_number)

        return db.session.scalar(statement)

    def get_for_landing(
        self,
        publication_status: PublicationStatus | None = None,
        *,
        visible_only: bool = False,
    ) -> list[Photo]:
        """Geef foto's voor de landingspagina, eventueel op status."""

        statement = select(Photo)

        if publication_status is not None:
            statement = statement.where(Photo.publication_status == publication_status)

        if visible_only:
            statement = statement.where(Photo.is_visible.is_(True))

        statement = statement.order_by(Photo.photo_number)

        return list(db.session.scalars(statement))

    def get_published(self) -> list[Photo]:
        """Geef alle gepubliceerde foto's."""

        statement = (
            select(Photo)
            .where(Photo.publication_status == PublicationStatus.PUBLISHED)
            .order_by(Photo.photo_number)
        )

        return list(db.session.scalars(statement))

    def get_previous(
        self,
        photo_number: str,
    ) -> Photo | None:
        """Vorige foto op fotonummer."""

        statement = (
            select(Photo)
            .where(Photo.photo_number < photo_number)
            .order_by(Photo.photo_number.desc())
            .limit(1)
        )

        return db.session.scalar(statement)

    def get_next(
        self,
        photo_number: str,
    ) -> Photo | None:
        """Volgende foto op fotonummer."""

        statement = (
            select(Photo)
            .where(Photo.photo_number > photo_number)
            .order_by(Photo.photo_number)
            .limit(1)
        )

        return db.session.scalar(statement)

    def count_by_status(
        self,
        publication_status: PublicationStatus,
    ) -> int:
        """Tel foto's met de opgegeven publicatiestatus."""

        statement = (
            select(func.count())
            .select_from(Photo)
            .where(Photo.publication_status == publication_status)
        )

        return db.session.scalar(statement) or 0
