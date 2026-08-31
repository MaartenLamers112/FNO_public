"""Gemeenschappelijke basis voor services."""

from __future__ import annotations


class BaseService[RepositoryType]:
    """Basisklasse voor services met een expliciete repositoryafhankelijkheid."""

    def __init__(self, repository: RepositoryType) -> None:
        """Bewaar de primaire repository van de service."""

        self.repository = repository

    def _commit(self) -> None:
        """Sla de volledige huidige databasetransactie op."""

        try:
            self.repository.save()
        except Exception:
            self.repository.rollback()
            raise
