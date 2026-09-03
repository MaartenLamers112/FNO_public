"""E-mailverificatie voor FNO-gebruikers."""

from __future__ import annotations

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.exceptions import ValidationError
from app.models import User
from app.repositories import UserRepository
from app.services.mail_service import MailService


class EmailVerificationService:
    """Maak, verstuur en verwerk verificatietokens."""

    TOKEN_SALT = "fno-email-verification"

    def __init__(
        self,
        repository: UserRepository | None = None,
        mail_service: MailService | None = None,
    ) -> None:
        """Initialiseer de service met standaard- of testafhankelijkheden."""

        self.repository = repository or UserRepository()
        self.mail_service = mail_service or MailService()

    def create_token(self, user: User) -> str:
        """Maak een ondertekend verificatietoken voor een gebruiker."""

        if not user.email:
            raise ValidationError(
                "Voor dit account is geen e-mailadres ingesteld.",
                code="EMAIL_REQUIRED",
            )

        return self._serializer().dumps({
            "user_id": user.id,
            "email": user.email,
        })

    def send_verification(self, user: User) -> None:
        """Stuur een verificatielink naar het accountadres."""

        if not user.email:
            raise ValidationError(
                "Voor dit account is geen e-mailadres ingesteld.",
                code="EMAIL_REQUIRED",
            )

        token = self.create_token(user)
        base_url = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
        verification_url = f"{base_url}/verify-email/{token}"

        self.mail_service.send_text(
            recipient=user.email,
            subject="Bevestig je e-mailadres voor Foto Nummeraar Online",
            body=(
                f"Hallo {user.username},\n\n"
                "Bevestig je e-mailadres voor Foto Nummeraar Online via deze link:\n"
                f"{verification_url}\n\n"
                "Deze link is 24 uur geldig.\n\n"
                "Heb je dit account niet aangemaakt, dan kun je dit bericht negeren."
            ),
        )

    def verify(self, token: str) -> User:
        """Bevestig het e-mailadres dat bij een geldig token hoort."""

        payload = self._load_token(token)
        user = self.repository.get(payload["user_id"])

        if user is None or user.email != payload["email"]:
            raise ValidationError(
                "Deze verificatielink is niet meer geldig.",
                code="INVALID_EMAIL_VERIFICATION_TOKEN",
            )

        if not user.email_verified:
            self.repository.set_email_verified(user, verified=True)
            self.repository.save()

        return user

    def resend(self, email: str) -> None:
        """Stuur opnieuw een verificatiebericht zonder accountinformatie te lekken."""

        normalized_email = email.strip().lower()
        if not normalized_email:
            return

        user = self.repository.get_by_email(normalized_email)
        if user is None or user.email_verified or not user.is_active:
            return

        self.send_verification(user)

    def _load_token(self, token: str) -> dict[str, object]:
        """Lees een geldig en niet-verlopen verificatietoken."""

        max_age = current_app.config["EMAIL_VERIFICATION_MAX_AGE_SECONDS"]

        try:
            payload = self._serializer().loads(token, max_age=max_age)
        except SignatureExpired as exc:
            raise ValidationError(
                "Deze verificatielink is verlopen.",
                code="EMAIL_VERIFICATION_TOKEN_EXPIRED",
            ) from exc
        except BadSignature as exc:
            raise ValidationError(
                "Deze verificatielink is ongeldig.",
                code="INVALID_EMAIL_VERIFICATION_TOKEN",
            ) from exc

        if (
            not isinstance(payload, dict)
            or not isinstance(payload.get("user_id"), int)
            or not isinstance(payload.get("email"), str)
        ):
            raise ValidationError(
                "Deze verificatielink is ongeldig.",
                code="INVALID_EMAIL_VERIFICATION_TOKEN",
            )

        return payload

    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        """Maak de serializer op basis van de applicatiesleutel."""

        return URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"],
            salt=EmailVerificationService.TOKEN_SALT,
        )
