"""Tests voor RoleRepository."""

from app.repositories import RoleRepository


def test_role_repository_can_create_and_find_role(app) -> None:
    """Een rol kan worden aangemaakt en op naam worden teruggevonden."""

    repository = RoleRepository()

    role = repository.create(
        name="employee",
        description="Medewerker",
    )
    repository.save()

    stored_role = repository.get_by_name("employee")

    assert stored_role is not None
    assert stored_role.id == role.id
    assert stored_role.name == "employee"
    assert stored_role.description == "Medewerker"


def test_role_repository_reports_existing_name(app) -> None:
    """De repository herkent een reeds gebruikte rolnaam."""

    repository = RoleRepository()

    repository.create(
        name="administrator",
        description="Beheerder",
    )
    repository.save()

    assert repository.exists_by_name("administrator")
    assert not repository.exists_by_name("visitor")


def test_role_repository_can_update_role(app) -> None:
    """Een bestaande rol kan worden gewijzigd."""

    repository = RoleRepository()

    role = repository.create(
        name="employee",
        description="Oude beschrijving",
    )
    repository.save()

    repository.update(
        role,
        description="Medewerker",
    )
    repository.save()

    stored_role = repository.get(role.id)

    assert stored_role is not None
    assert stored_role.description == "Medewerker"


def test_role_repository_can_return_all_roles(app) -> None:
    """Alle rollen worden op ID-volgorde teruggegeven."""

    repository = RoleRepository()

    repository.create(name="visitor")
    repository.create(name="employee")
    repository.create(name="administrator")
    repository.save()

    roles = repository.get_all()

    assert [role.name for role in roles] == [
        "visitor",
        "employee",
        "administrator",
    ]


def test_role_repository_can_delete_role(app) -> None:
    """Een rol kan worden verwijderd."""

    repository = RoleRepository()

    role = repository.create(name="temporary")
    repository.save()

    role_id = role.id

    repository.delete(role)
    repository.save()

    assert repository.get(role_id) is None
