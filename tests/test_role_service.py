"""Tests voor RoleService."""

from unittest.mock import Mock

import pytest

from app.exceptions import (
    ConflictError,
    ValidationError,
)
from app.models import Role
from app.repositories import RoleRepository
from app.services import RoleService


def test_role_service_can_create_role(app) -> None:
    """Een geldige rol wordt opgeslagen."""

    service = RoleService()

    role = service.create(
        name="employee",
        description="Medewerker",
    )

    assert role.id is not None
    assert role.name == "employee"
    assert role.description == "Medewerker"


def test_duplicate_role_name_is_not_allowed(app) -> None:
    """Dubbele rolnamen worden geweigerd."""

    service = RoleService()

    service.create(name="administrator")

    with pytest.raises(ConflictError) as exc:
        service.create(name="administrator")

    assert exc.value.code == "ROLE_ALREADY_EXISTS"
    assert exc.value.details == {
        "role_name": "administrator",
    }


def test_empty_role_name_is_not_allowed(app) -> None:
    """Een lege rolnaam wordt geweigerd."""

    service = RoleService()

    with pytest.raises(ValidationError) as exc:
        service.create(name="   ")

    assert exc.value.code == "ROLE_NAME_REQUIRED"
    assert exc.value.details == {}


def test_role_service_normalizes_input(app) -> None:
    """Voor- en achterliggende witruimte wordt verwijderd."""

    service = RoleService()

    role = service.create(
        name="  employee  ",
        description="  Medewerker  ",
    )

    assert role.name == "employee"
    assert role.description == "Medewerker"


def test_role_service_can_update_role(app) -> None:
    """Een bestaande rol kan worden gewijzigd."""

    service = RoleService()

    role = service.create(
        name="employee",
        description="Oude beschrijving",
    )

    updated_role = service.update(
        role,
        description="Medewerker",
    )

    assert updated_role.description == "Medewerker"


def test_role_service_accepts_injected_repository() -> None:
    """Een repository kan voor tests expliciet worden geïnjecteerd."""

    repository = Mock(spec=RoleRepository)
    role = Role(
        name="employee",
        description="Medewerker",
    )

    repository.exists_by_name.return_value = False
    repository.create.return_value = role

    service = RoleService(repository=repository)

    result = service.create(
        name="employee",
        description="Medewerker",
    )

    assert result is role

    repository.exists_by_name.assert_called_once_with("employee")
    repository.create.assert_called_once_with(
        name="employee",
        description="Medewerker",
    )
    repository.save.assert_called_once_with()
