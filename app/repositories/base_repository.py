"""Generieke basisrepository voor SQLAlchemy-entiteiten."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute

from app.extensions import db


class BaseRepository[T]:
    """Generieke repository met standaard databasebewerkingen."""

    model: type[T] | None = None

    def __init__(self) -> None:
        """Controleer of de concrete repository een model definieert."""

        if self.model is None:
            raise ValueError(
                "Een repository-subklasse moet het attribuut 'model' definiëren."
            )

    def get(self, entity_id: int) -> T | None:
        """Haal één entiteit op via de primaire sleutel."""

        return db.session.get(self.model, entity_id)

    def get_all(self) -> list[T]:
        """Geef alle entiteiten terug, gesorteerd op primaire sleutel."""

        statement = select(self.model).order_by(self.model.id)

        return list(db.session.scalars(statement))

    def add(self, entity: T) -> T:
        """Voeg een entiteit toe aan de huidige databasesessie."""

        db.session.add(entity)
        return entity

    def delete(self, entity: T) -> None:
        """Markeer een entiteit voor verwijdering."""

        db.session.delete(entity)

    def flush(self) -> None:
        """Stuur pending wijzigingen naar de database zonder te committen."""

        db.session.flush()

    def save(self) -> None:
        """Sla de huidige transactie op."""

        db.session.commit()

    def rollback(self) -> None:
        """Draai de huidige transactie terug."""

        db.session.rollback()

    def count(self) -> int:
        """Geef het totale aantal entiteiten terug."""

        statement = select(func.count()).select_from(self.model)

        return db.session.scalar(statement) or 0

    def exists(self, entity_id: int) -> bool:
        """Controleer of een entiteit met deze primaire sleutel bestaat."""

        statement = select(self.model.id).where(self.model.id == entity_id).limit(1)

        return db.session.scalar(statement) is not None

    def exists_by(
        self,
        column: InstrumentedAttribute[Any],
        value: object,
    ) -> bool:
        """Controleer generiek of een kolomwaarde bestaat."""

        statement = select(self.model.id).where(column == value).limit(1)

        return db.session.scalar(statement) is not None
