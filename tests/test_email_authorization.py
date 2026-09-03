"""Tests voor autorisatie van onbevestigde accounts."""

from flask_login import login_user

from app.exceptions import AuthorizationError
from app.services import AuthorizationService, UserService


def test_unverified_registered_user_cannot_contribute(app) -> None:
    """Een geregistreerde gebruiker moet eerst het e-mailadres bevestigen."""

    user = UserService().register_user(
        username="gebruiker",
        email="gebruiker@example.nl",
        password="veilig123",
    )

    with app.test_request_context():
        login_user(user)

        try:
            AuthorizationService().require_contribution()
        except AuthorizationError as error:
            assert error.code == "EMAIL_VERIFICATION_REQUIRED"
        else:
            raise AssertionError("AuthorizationError verwacht.")


def test_legacy_user_without_email_keeps_access(app) -> None:
    """Een bestaand medewerkeraccount zonder e-mailadres blijft werken."""

    user = UserService().create_user(
        username="medewerker",
        password="veilig123",
        role_name="employee",
    )

    with app.test_request_context():
        login_user(user)

        AuthorizationService().require_contribution()
