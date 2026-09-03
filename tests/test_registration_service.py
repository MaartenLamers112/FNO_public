"""Tests voor registratie en e-mailverificatie."""

from app.exceptions import ValidationError
from app.repositories import UserRepository
from app.services import EmailVerificationService, RegistrationService, UserService


class RecordingVerificationService:
    """Testdubbel dat verstuurde verificaties onthoudt."""

    def __init__(self) -> None:
        self.sent_user_ids: list[int] = []

    def send_verification(self, user) -> None:
        """Onthoud voor welke gebruiker een mail zou worden verstuurd."""

        self.sent_user_ids.append(user.id)


def test_registration_creates_unverified_user(app) -> None:
    """Registratie maakt een onbevestigde gewone gebruiker aan."""

    verification = RecordingVerificationService()
    service = RegistrationService(
        user_service=UserService(),
        verification_service=verification,
    )

    user = service.register(
        username=" nieuwe gebruiker ",
        email=" Gebruiker@Example.NL ",
        password="veilig123",
        password_confirmation="veilig123",
    )

    assert user.username == "nieuwe gebruiker"
    assert user.email == "gebruiker@example.nl"
    assert user.email_verified is False
    assert user.role.name == "user"
    assert verification.sent_user_ids == [user.id]


def test_registration_rejects_password_mismatch(app) -> None:
    """Verschillende wachtwoorden worden geweigerd."""

    try:
        RegistrationService().register(
            username="gebruiker",
            email="gebruiker@example.nl",
            password="veilig123",
            password_confirmation="anders123",
        )
    except ValidationError as error:
        assert error.code == "PASSWORD_CONFIRMATION_MISMATCH"
    else:
        raise AssertionError("ValidationError verwacht.")


def test_registration_rejects_invalid_email(app) -> None:
    """Een ongeldig e-mailadres wordt geweigerd."""

    try:
        UserService().register_user(
            username="gebruiker",
            email="ongeldig",
            password="veilig123",
        )
    except ValidationError as error:
        assert error.code == "INVALID_EMAIL"
    else:
        raise AssertionError("ValidationError verwacht.")


def test_email_verification_marks_user_verified(app) -> None:
    """Een geldig token bevestigt het bijbehorende e-mailadres."""

    user = UserService().register_user(
        username="gebruiker",
        email="gebruiker@example.nl",
        password="veilig123",
    )
    service = EmailVerificationService()
    token = service.create_token(user)

    verified_user = service.verify(token)

    assert verified_user.id == user.id
    assert UserRepository().get(user.id).email_verified is True


def test_email_verification_rejects_invalid_token(app) -> None:
    """Een ongeldig token wordt geweigerd."""

    try:
        EmailVerificationService().verify("ongeldig-token")
    except ValidationError as error:
        assert error.code == "INVALID_EMAIL_VERIFICATION_TOKEN"
    else:
        raise AssertionError("ValidationError verwacht.")
