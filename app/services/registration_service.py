"""Registratieworkflow voor openbare FNO-gebruikers."""

from __future__ import annotations

from app.exceptions import ValidationError
from app.models import User
from app.services.email_verification_service import EmailVerificationService
from app.services.user_service import UserService


class RegistrationService:
    """Registreer gebruikers en handel e-mailverificatie af."""

    def __init__(
        self,
        user_service: UserService | None = None,
        verification_service: EmailVerificationService | None = None,
    ) -> None:
        """Initialiseer de registratieworkflow."""

        self.user_service = user_service or UserService()
        self.verification_service = verification_service or EmailVerificationService()

    def register(
        self,
        *,
        username: str,
        email: str,
        password: str,
        password_confirmation: str,
    ) -> User:
        """Maak een gebruikersaccount aan en stuur de verificatiemail."""

        if password != password_confirmation:
            raise ValidationError(
                "De wachtwoorden zijn niet gelijk.",
                code="PASSWORD_CONFIRMATION_MISMATCH",
            )

        user = self.user_service.register_user(
            username=username,
            email=email,
            password=password,
        )
        self.verification_service.send_verification(user)
        return user

    def verify_email(self, token: str) -> User:
        """Bevestig een e-mailadres via een verificatietoken."""

        return self.verification_service.verify(token)

    def resend_verification(self, email: str) -> None:
        """Stuur opnieuw een verificatiebericht."""

        self.verification_service.resend(email)
