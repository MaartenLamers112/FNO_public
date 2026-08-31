"""Repository voor gebruikersrollen."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.models import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Databasebewerkingen voor de Role-entiteit."""

    model = Role

    def get_by_name(self, name: str) -> Role | None:
        """Haal een rol op via de unieke rolnaam."""

        statement = select(Role).where(Role.name == name)

        return db.session.scalar(statement)

    def exists_by_name(self, name: str) -> bool:
        """Controleer of een rolnaam al bestaat."""

        return self.exists_by(Role.name, name)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Role:
        """Maak een rol aan en voeg deze toe aan de sessie."""

        role = Role(
            name=name,
            description=description,
        )

        return self.add(role)

    def update(
        self,
        role: Role,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        """Werk de opgegeven rolvelden bij."""

        if name is not None:
            role.name = name

        if description is not None:
            role.description = description

        return role
