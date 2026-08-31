"""Bedrijfslogica voor gebruikersrollen."""

from __future__ import annotations

from app.exceptions import (
    ConflictError,
    ValidationError,
)
from app.models import Role
from app.repositories import RoleRepository
from app.services.base_service import BaseService


class RoleService(BaseService[RoleRepository]):
    """Bedrijfslogica rondom gebruikersrollen."""

    def __init__(
        self,
        repository: RoleRepository | None = None,
    ) -> None:
        """Initialiseer de service met de standaard- of testrepository."""

        super().__init__(repository=repository or RoleRepository())

    def get(self, role_id: int) -> Role | None:
        """Haal een rol op via de primaire sleutel."""

        return self.repository.get(role_id)

    def get_all(self) -> list[Role]:
        """Geef alle rollen terug."""

        return self.repository.get_all()

    def get_by_name(self, name: str) -> Role | None:
        """Zoek een rol op de interne rolnaam."""

        return self.repository.get_by_name(name)

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Role:
        """Maak een nieuwe rol aan."""

        normalized_name = name.strip()

        if not normalized_name:
            raise ValidationError(
                "De rolnaam is verplicht.",
                code="ROLE_NAME_REQUIRED",
            )

        if self.repository.exists_by_name(normalized_name):
            raise ConflictError(
                f"Rol '{normalized_name}' bestaat al.",
                code="ROLE_ALREADY_EXISTS",
                details={
                    "role_name": normalized_name,
                },
            )

        role = self.repository.create(
            name=normalized_name,
            description=(description.strip() if description is not None else None),
        )

        self.repository.save()

        return role

    def update(
        self,
        role: Role,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        """Wijzig een bestaande rol."""

        normalized_name = name.strip() if name is not None else None

        if normalized_name == "":
            raise ValidationError(
                "De rolnaam is verplicht.",
                code="ROLE_NAME_REQUIRED",
            )

        if (
            normalized_name is not None
            and normalized_name != role.name
            and self.repository.exists_by_name(normalized_name)
        ):
            raise ConflictError(
                f"Rol '{normalized_name}' bestaat al.",
                code="ROLE_ALREADY_EXISTS",
                details={
                    "role_name": normalized_name,
                },
            )

        updated_role = self.repository.update(
            role,
            name=normalized_name,
            description=(description.strip() if description is not None else None),
        )

        self.repository.save()

        return updated_role

    def delete(self, role: Role) -> None:
        """Verwijder een rol."""

        self.repository.delete(role)
        self.repository.save()
