"""Centrale rolgebaseerde autorisatie voor FNO."""

from __future__ import annotations

from flask_login import current_user

from app.exceptions import AuthorizationError


class AuthorizationService:
    """Controleer centraal of de huidige gebruiker een actie mag uitvoeren."""

    USER_ROLE = "user"
    EMPLOYEE_ROLE = "employee"
    ADMINISTRATOR_ROLE = "administrator"

    def can_contribute(self) -> bool:
        """Geef aan of de huidige gebruiker inhoud mag bijdragen."""

        if not self.has_any_role(
            self.USER_ROLE,
            self.EMPLOYEE_ROLE,
            self.ADMINISTRATOR_ROLE,
        ):
            return False

        return self._has_verified_email_when_required()

    def can_view_hidden_photos(self) -> bool:
        """Geef aan of verborgen foto's zichtbaar mogen zijn."""

        return self.can_manage_labels()

    def can_manage_labels(self) -> bool:
        """Geef aan of de huidige gebruiker persoonslabels mag beheren."""

        return self.has_any_role(
            self.EMPLOYEE_ROLE,
            self.ADMINISTRATOR_ROLE,
        )

    def can_administer(self) -> bool:
        """Geef aan of de huidige gebruiker beheerder is."""

        return self.has_any_role(self.ADMINISTRATOR_ROLE)

    def can_manage_publication(self) -> bool:
        """Geef aan of de huidige gebruiker publicatiestatus mag beheren."""

        return self.can_administer()

    def require_contribution(self) -> None:
        """Vereis minimaal een geverifieerde ingelogde FNO-gebruiker."""

        if not current_user.is_authenticated:
            raise AuthorizationError(
                "Aanmelden is vereist voor deze actie.",
                code="AUTHENTICATION_REQUIRED",
            )

        if not self._has_verified_email_when_required():
            raise AuthorizationError(
                "Bevestig eerst je e-mailadres om wijzigingen te kunnen doen.",
                code="EMAIL_VERIFICATION_REQUIRED",
            )

        if not self.can_contribute():
            raise AuthorizationError(
                "Je hebt onvoldoende rechten voor deze actie.",
                code="FORBIDDEN",
            )

    def require_publication_management(self) -> None:
        """Vereis de beheerdersrol voor publicatiebeheer."""

        self.require_administrator()

    def require_administrator(self) -> None:
        """Vereis de beheerdersrol."""

        if not current_user.is_authenticated:
            raise AuthorizationError(
                "Aanmelden is vereist voor deze actie.",
                code="AUTHENTICATION_REQUIRED",
            )

        if not self.can_administer():
            raise AuthorizationError(
                "Je hebt onvoldoende rechten voor deze actie.",
                code="FORBIDDEN",
            )

    def require_label_management(self) -> None:
        """Vereis minimaal de medewerkersrol voor labelbeheer."""

        if not current_user.is_authenticated:
            raise AuthorizationError(
                "Aanmelden is vereist voor deze actie.",
                code="AUTHENTICATION_REQUIRED",
            )

        if not self.can_manage_labels():
            raise AuthorizationError(
                "Je hebt onvoldoende rechten voor deze actie.",
                code="FORBIDDEN",
            )

    def has_any_role(self, *role_names: str) -> bool:
        """Controleer of de huidige gebruiker één van de rollen heeft."""

        if not current_user.is_authenticated:
            return False

        role = getattr(current_user, "role", None)
        return role is not None and role.name in role_names

    @staticmethod
    def _has_verified_email_when_required() -> bool:
        """Behoud legacyaccounts en vereis verificatie zodra e-mail bestaat."""

        email = getattr(current_user, "email", None)
        if email is None:
            return True

        return bool(getattr(current_user, "email_verified", False))
