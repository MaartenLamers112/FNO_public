"""Tests voor UserRepository."""

from datetime import UTC, datetime

from werkzeug.security import generate_password_hash

from app.repositories import RoleRepository, UserRepository


def create_role() -> int:
    """Maak een medewerkersrol aan en geef de ID terug."""

    role_repository = RoleRepository()

    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    return role.id


def test_user_repository_can_create_and_find_user(app) -> None:
    """Een gebruiker kan worden aangemaakt en teruggevonden."""

    role_id = create_role()
    repository = UserRepository()

    password_hash = generate_password_hash("veilig-testwachtwoord")

    user = repository.create(
        username="medewerker",
        password_hash=password_hash,
        role_id=role_id,
    )
    repository.save()

    stored_user = repository.get_by_username("medewerker")

    assert stored_user is not None
    assert stored_user.id == user.id
    assert stored_user.username == "medewerker"
    assert stored_user.role_id == role_id
    assert stored_user.is_active is True
    assert stored_user.check_password("veilig-testwachtwoord")


def test_user_repository_reports_existing_username(app) -> None:
    """De repository herkent een gebruikte gebruikersnaam."""

    role_id = create_role()
    repository = UserRepository()

    repository.create(
        username="beheer",
        password_hash=generate_password_hash("testwachtwoord"),
        role_id=role_id,
    )
    repository.save()

    assert repository.exists_by_username("beheer")
    assert not repository.exists_by_username("onbekend")


def test_user_repository_can_update_user(app) -> None:
    """Een bestaande gebruiker kan worden gewijzigd."""

    role_id = create_role()
    repository = UserRepository()

    user = repository.create(
        username="oude_naam",
        password_hash=generate_password_hash("testwachtwoord"),
        role_id=role_id,
    )
    repository.save()

    repository.update(
        user,
        username="nieuwe_naam",
        is_active=False,
    )
    repository.save()

    stored_user = repository.get(user.id)

    assert stored_user is not None
    assert stored_user.username == "nieuwe_naam"
    assert stored_user.is_active is False


def test_user_repository_can_update_last_login(app) -> None:
    """Het laatste succesvolle loginmoment kan worden opgeslagen."""

    role_id = create_role()
    repository = UserRepository()

    user = repository.create(
        username="medewerker",
        password_hash=generate_password_hash("testwachtwoord"),
        role_id=role_id,
    )
    repository.save()

    login_time = datetime(
        2026,
        7,
        15,
        18,
        30,
        tzinfo=UTC,
    )

    repository.update_last_login(
        user,
        logged_in_at=login_time,
    )
    repository.save()

    stored_user = repository.get(user.id)

    assert stored_user is not None
    assert stored_user.last_login == login_time.replace(tzinfo=None)


def test_user_repository_can_delete_user(app) -> None:
    """Een gebruiker kan worden verwijderd."""

    role_id = create_role()
    repository = UserRepository()

    user = repository.create(
        username="tijdelijk",
        password_hash=generate_password_hash("testwachtwoord"),
        role_id=role_id,
    )
    repository.save()

    user_id = user.id

    repository.delete(user)
    repository.save()

    assert repository.get(user_id) is None
