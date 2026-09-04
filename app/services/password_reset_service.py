"""Wachtwoordherstel voor FNO-gebruikers."""

from __future__ import annotations

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.exceptions import ValidationError
from app.models import User
from app.repositories import UserRepository
from app.services.mail_service import MailService
from app.services.user_service import UserService


class PasswordResetService:
    """Maak, verstuur en verwerk wachtwoordhersteltokens."""

    TOKEN_SALT = "fno-password-reset"

    def __init__(
        self,
        repository: UserRepository | None = None,
        mail_service: MailService | None = None,
        user_service: UserService | None = None,
    ) -> None:
        """Initialiseer de service met standaard- of testafhankelijkheden."""

        self.repository = repository or UserRepository()
        self.mail_service = mail_service or MailService()
        self.user_service = user_service or UserService(repository=self.repository)

    def request_reset(self, email: str) -> None:
        """Stuur zo nodig een resetmail zonder accountinformatie te lekken."""

        normalized_email = email.strip().lower()
        if not normalized_email:
            return

        user = self.repository.get_by_email(normalized_email)
        if user is None or not user.is_active or not user.email:
            return

        self.send_reset(user)

    def create_token(self, user: User) -> str:
        """Maak een token dat na wachtwoordwijziging ongeldig wordt."""

        if not user.email:
            raise ValidationError(
                "Voor dit account is geen e-mailadres ingesteld.",
                code="EMAIL_REQUIRED",
            )

        return self._serializer().dumps({
            "user_id": user.id,
            "email": user.email,
            "password_hash": user.password_hash,
        })

    def send_reset(self, user: User) -> None:
        """Stuur een wachtwoordherst link naar het accountadres."""

        if not user.email:
            raise ValidationError(
                "Voor dit account is geen e-mailadres ingesteld.",
                code="EMAIL_REQUIRED",
            )

        token = self.create_token(user)
        base_url = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
        reset_url = f"{base_url}/password/reset/{token}"

        self.mail_service.send_text(
            recipient=user.email,
            subject="Wachtwoord herstellen voor Foto Nummeraar Online",
            body=(
                f"Hallo {user.username},\n\n"
                "Gebruik deze link om een nieuw wachtwoord in te stellen:\n"
                f"{reset_url}\n\n"
                "Deze link is 1 uur geldig.\n\n"
                "Heb je dit niet aangevraagd, dan kun je dit bericht negeren."
            ),
        )

    def validate_token(self, token: str) -> User:
        """Geef de gebruiker terug als het token geldig en actueel is."""

        payload = self._load_token(token)
        user = self.repository.get(payload["user_id"])

        if (
            user is None
            or not user.is_active
            or user.email != payload["email"]
            or user.password_hash != payload["password_hash"]
        ):
            raise ValidationError(
                "Deze wachtwoordlink is niet meer geldig.",
                code="INVALID_PASSWORD_RESET_TOKEN",
            )

        return user

    def reset_password(
        self,
        token: str,
        *,
        password: str,
        password_confirmation: str,
    ) -> User:
        """Stel via een geldig token een nieuw wachtwoord in."""

        if password != password_confirmation:
            raise ValidationError(
                "De nieuwe wachtwoorden zijn niet gelijk.",
                code="PASSWORD_CONFIRMATION_MISMATCH",
            )

        user = self.validate_token(token)
        return self.user_service.reset_password(user.id, password=password)

    def _load_token(self, token: str) -> dict[str, object]:
        """Lees een geldig en niet-verlopen wachtwoordhersteltoken."""

        max_age = current_app.config["PASSWORD_RESET_MAX_AGE_SECONDS"]

        try:
            payload = self._serializer().loads(token, max_age=max_age)
        except SignatureExpired as exc:
            raise ValidationError(
                "Deze wachtwoordlink is verlopen.",
                code="PASSWORD_RESET_TOKEN_EXPIRED",
            ) from exc
        except BadSignature as exc:
            raise ValidationError(
                "Deze wachtwoordlink is ongeldig.",
                code="INVALID_PASSWORD_RESET_TOKEN",
            ) from exc

        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("user_id"), int)
            or not isinstance(payload.get("email"), str)
            or not isinstance(payload.get("password_hash"), str)
        ):
            raise ValidationError(
                "Deze wachtwoordlink is ongeldig.",
                code="INVALID_PASSWORD_RESET_TOKEN",
            )

        return payload

    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        """Maak de serializer op basis van de applicatiesleutel."""

        return URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"],
            salt=PasswordResetService.TOKEN_SALT,
        )
