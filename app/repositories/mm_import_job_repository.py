"""Repository voor MM-importopdrachten."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.models import MmImportJob
from app.repositories.base_repository import BaseRepository


class MmImportJobRepository(BaseRepository[MmImportJob]):
    """Databasebewerkingen voor MM-importopdrachten."""

    model = MmImportJob

    def get_recent(self, *, limit: int = 20) -> list[MmImportJob]:
        """Geef recente importopdrachten terug."""

        statement = (
            select(MmImportJob)
            .order_by(MmImportJob.created_at.desc(), MmImportJob.id.desc())
            .limit(limit)
        )
        return list(db.session.scalars(statement))
