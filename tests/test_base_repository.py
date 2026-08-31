"""Tests voor de generieke BaseRepository-functionaliteit."""

from app.repositories import RoleRepository


def test_base_repository_count(app) -> None:
    """De repository telt het aantal records correct."""

    repository = RoleRepository()

    repository.create(name="visitor")
    repository.create(name="employee")
    repository.save()

    assert repository.count() == 2


def test_base_repository_exists(app) -> None:
    """De repository controleert bestaan via de primaire sleutel."""

    repository = RoleRepository()

    role = repository.create(name="administrator")
    repository.save()

    assert repository.exists(role.id)
    assert not repository.exists(999999)


def test_base_repository_exists_by(app) -> None:
    """De generieke kolomcontrole herkent bestaande waarden."""

    repository = RoleRepository()

    repository.create(name="employee")
    repository.save()

    assert repository.exists_by_name("employee")
    assert not repository.exists_by_name("visitor")
