"""Tests voor UserService."""

from app.exceptions import AuthorizationError, ConflictError, ValidationError
from app.repositories import RoleRepository, UserRepository
from app.services import UserService


def create_user(
    *,
    username: str = "medewerker",
    password: str = "veilig-testwachtwoord",
    is_active: bool = True,
):
    """Maak een testgebruiker met medewerkersrol aan."""

    role_repository = RoleRepository()
    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    user_repository = UserRepository()
    user = user_repository.create(
        username=username,
        password_hash="tijdelijk",
        role_id=role.id,
        is_active=is_active,
    )
    user.set_password(password)
    user_repository.save()

    return user


def test_user_service_authenticates_active_user(app) -> None:
    """Een actieve gebruiker kan met geldige gegevens aanmelden."""

    created_user = create_user()

    user = UserService().authenticate(
        username=" medewerker ",
        password="veilig-testwachtwoord",
    )

    assert user.id == created_user.id
    assert user.last_login is not None


def test_user_service_rejects_missing_login_fields(app) -> None:
    """Lege aanmeldgegevens worden geweigerd."""

    try:
        UserService().authenticate(username="", password="")
    except ValidationError as error:
        assert error.code == "LOGIN_FIELDS_REQUIRED"
    else:
        raise AssertionError("ValidationError verwacht.")


def test_user_service_rejects_invalid_credentials(app) -> None:
    """Een onjuist wachtwoord geeft geen informatie over het account prijs."""

    create_user()

    try:
        UserService().authenticate(
            username="medewerker",
            password="verkeerd",
        )
    except AuthorizationError as error:
        assert error.code == "INVALID_CREDENTIALS"
    else:
        raise AssertionError("AuthorizationError verwacht.")


def test_user_service_rejects_unknown_user(app) -> None:
    """Een onbekende gebruiker krijgt dezelfde generieke foutmelding."""

    try:
        UserService().authenticate(
            username="onbekend",
            password="willekeurig",
        )
    except AuthorizationError as error:
        assert error.code == "INVALID_CREDENTIALS"
    else:
        raise AssertionError("AuthorizationError verwacht.")


def test_user_service_rejects_inactive_user(app) -> None:
    """Een gedeactiveerd account kan niet aanmelden."""

    create_user(is_active=False)

    try:
        UserService().authenticate(
            username="medewerker",
            password="veilig-testwachtwoord",
        )
    except AuthorizationError as error:
        assert error.code == "USER_INACTIVE"
    else:
        raise AssertionError("AuthorizationError verwacht.")


def test_user_service_creates_administrator(app) -> None:
    """Een beheerder krijgt automatisch de juiste rol en wachtwoordhash."""

    user = UserService().create_administrator(
        username=" beheerder ",
        password="zeer-veilig-wachtwoord",
    )

    assert user.username == "beheerder"
    assert user.role.name == "administrator"
    assert user.is_active is True
    assert user.check_password("zeer-veilig-wachtwoord") is True


def test_user_service_rejects_duplicate_administrator(app) -> None:
    """Een bestaande gebruikersnaam kan niet opnieuw worden aangemaakt."""

    service = UserService()
    service.create_administrator(
        username="beheerder",
        password="zeer-veilig-wachtwoord",
    )

    try:
        service.create_administrator(
            username="beheerder",
            password="ander-veilig-wachtwoord",
        )
    except ConflictError as error:
        assert error.code == "USER_ALREADY_EXISTS"
        assert error.details == {"username": "beheerder"}
    else:
        raise AssertionError("ConflictError verwacht.")


def test_user_service_rejects_short_admin_password(app) -> None:
    """Een beheerder kan niet met een te kort wachtwoord worden aangemaakt."""

    try:
        UserService().create_administrator(
            username="beheerder",
            password="abc",
        )
    except ValidationError as error:
        assert error.code == "PASSWORD_TOO_SHORT"
        assert error.details == {"minimum_length": 4}
    else:
        raise AssertionError("ValidationError verwacht.")


def test_user_service_creates_employee(app) -> None:
    """Gebruikersbeheer kan een medewerker aanmaken."""

    user = UserService().create_user(
        username=" nieuwe medewerker ",
        password="veilig",
        role_name="employee",
    )

    assert user.username == "nieuwe medewerker"
    assert user.role.name == "employee"
    assert user.check_password("veilig") is True


def test_user_service_updates_managed_user(app) -> None:
    """Een beheerder kan rol en activatiestatus laten wijzigen."""

    user = create_user()
    admin_role = RoleRepository().create(name="administrator", description="Beheerder")
    RoleRepository().save()

    updated = UserService().update_user(
        user.id,
        username="gewijzigd",
        role_name="administrator",
        is_active=False,
        acting_user_id=999,
    )

    assert updated.username == "gewijzigd"
    assert updated.role_id == admin_role.id
    assert updated.is_active is False


def test_user_service_prevents_restricting_own_admin_account(app) -> None:
    """Een beheerder kan het eigen beheeraccount niet uitschakelen."""

    user = UserService().create_administrator(username="beheerder", password="veilig")

    try:
        UserService().update_user(
            user.id,
            username=user.username,
            role_name="administrator",
            is_active=False,
            acting_user_id=user.id,
        )
    except ValidationError as error:
        assert error.code == "CANNOT_RESTRICT_OWN_ADMIN_ACCOUNT"
    else:
        raise AssertionError("ValidationError verwacht.")


def test_user_service_changes_own_password(app) -> None:
    """Een gebruiker kan met het huidige wachtwoord een nieuw wachtwoord instellen."""

    user = create_user(password="oud-wachtwoord")

    UserService().change_own_password(
        user.id,
        current_password="oud-wachtwoord",
        new_password="nieuw-wachtwoord",
    )

    assert user.check_password("nieuw-wachtwoord") is True
