"""Bedrijfslogica voor geauthenticeerde FNO-gebruikers."""

from __future__ import annotations

from app.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models import User
from app.repositories import RoleRepository, UserRepository
from app.services.base_service import BaseService


class UserService(BaseService[UserRepository]):
    """Bedrijfslogica rondom gebruikers en authenticatie."""

    MINIMUM_PASSWORD_LENGTH = 8
    USER_ROLE_NAME = "user"
    USER_ROLE_DESCRIPTION = "Gebruiker"
    EMPLOYEE_ROLE_NAME = "employee"
    EMPLOYEE_ROLE_DESCRIPTION = "Medewerker"
    ADMINISTRATOR_ROLE_NAME = "administrator"
    ADMINISTRATOR_ROLE_DESCRIPTION = "Beheerder"
    MANAGED_ROLE_NAMES = {
        USER_ROLE_NAME,
        EMPLOYEE_ROLE_NAME,
        ADMINISTRATOR_ROLE_NAME,
    }

    def __init__(
        self,
        repository: UserRepository | None = None,
        role_repository: RoleRepository | None = None,
    ) -> None:
        """Initialiseer de service met standaard- of testrepositories."""

        super().__init__(repository=repository or UserRepository())
        self.role_repository = role_repository or RoleRepository()

    def authenticate(self, *, username: str, password: str) -> User:
        """Authenticeer een actieve gebruiker en registreer de login."""

        normalized_username = username.strip()
        if not normalized_username or not password:
            raise ValidationError(
                "Gebruikersnaam en wachtwoord zijn verplicht.",
                code="LOGIN_FIELDS_REQUIRED",
            )
        user = self.repository.get_by_username(normalized_username)
        if user is None or not user.check_password(password):
            raise AuthorizationError(
                "De gebruikersnaam of het wachtwoord is onjuist.",
                code="INVALID_CREDENTIALS",
            )
        if not user.is_active:
            raise AuthorizationError(
                "Dit gebruikersaccount is niet actief.",
                code="USER_INACTIVE",
            )
        self.repository.update_last_login(user)
        self.repository.save()
        return user

    def list_users(self) -> list[User]:
        """Geef alle beheerde gebruikers terug."""

        return self.repository.get_all()

    def create_user(self, *, username: str, password: str, role_name: str) -> User:
        """Maak een medewerker of beheerder aan."""

        normalized_username = username.strip()
        self._validate_new_user(username=normalized_username, password=password)
        role = self._get_managed_role(role_name)
        user = self.repository.create(
            username=normalized_username,
            password_hash="tijdelijk",
            role_id=role.id,
        )
        user.set_password(password)
        self.repository.save()
        return user

    def create_administrator(self, *, username: str, password: str) -> User:
        """Maak een actieve gebruiker met de beheerdersrol aan."""

        return self.create_user(
            username=username,
            password=password,
            role_name=self.ADMINISTRATOR_ROLE_NAME,
        )

    def update_user(
        self,
        user_id: int,
        *,
        username: str,
        role_name: str,
        is_active: bool,
        acting_user_id: int,
    ) -> User:
        """Wijzig gebruikersnaam, rol en activatiestatus."""

        user = self._get_user(user_id)
        normalized_username = username.strip()
        if not normalized_username:
            raise ValidationError(
                "De gebruikersnaam is verplicht.",
                code="USERNAME_REQUIRED",
            )
        existing = self.repository.get_by_username(normalized_username)
        if existing is not None and existing.id != user.id:
            raise ConflictError(
                f"Gebruiker '{normalized_username}' bestaat al.",
                code="USER_ALREADY_EXISTS",
                details={"username": normalized_username},
            )
        if user.id == acting_user_id and (
            not is_active or role_name != self.ADMINISTRATOR_ROLE_NAME
        ):
            raise ValidationError(
                "Je kunt je eigen beheerdersaccount niet deactiveren of degraderen.",
                code="CANNOT_RESTRICT_OWN_ADMIN_ACCOUNT",
            )
        role = self._get_managed_role(role_name)
        self.repository.update(
            user,
            username=normalized_username,
            role_id=role.id,
            is_active=is_active,
        )
        self.repository.save()
        return user

    def reset_password(self, user_id: int, *, password: str) -> User:
        """Stel als beheerder een nieuw wachtwoord in."""

        self._validate_password(password)
        user = self._get_user(user_id)
        user.set_password(password)
        self.repository.save()
        return user

    def change_own_password(
        self,
        user_id: int,
        *,
        current_password: str,
        new_password: str,
    ) -> User:
        """Wijzig het eigen wachtwoord na controle van het huidige wachtwoord."""

        user = self._get_user(user_id)
        if not user.check_password(current_password):
            raise AuthorizationError(
                "Het huidige wachtwoord is onjuist.",
                code="INVALID_CURRENT_PASSWORD",
            )
        self._validate_password(new_password)
        user.set_password(new_password)
        self.repository.save()
        return user

    def _get_user(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if user is None:
            raise NotFoundError("Gebruiker niet gevonden.", code="USER_NOT_FOUND")
        return user

    def _get_managed_role(self, role_name: str):
        if role_name not in self.MANAGED_ROLE_NAMES:
            raise ValidationError("Ongeldige gebruikersrol.", code="INVALID_USER_ROLE")
        role = self.role_repository.get_by_name(role_name)
        if role is None:
            descriptions = {
                self.USER_ROLE_NAME: self.USER_ROLE_DESCRIPTION,
                self.EMPLOYEE_ROLE_NAME: self.EMPLOYEE_ROLE_DESCRIPTION,
                self.ADMINISTRATOR_ROLE_NAME: self.ADMINISTRATOR_ROLE_DESCRIPTION,
            }
            role = self.role_repository.create(
                name=role_name,
                description=descriptions[role_name],
            )
            self.role_repository.flush()
        return role

    def _validate_new_user(self, *, username: str, password: str) -> None:
        """Valideer de gegevens voor een nieuwe gebruiker."""

        if not username:
            raise ValidationError(
                "De gebruikersnaam is verplicht.",
                code="USERNAME_REQUIRED",
            )
        if self.repository.exists_by_username(username):
            raise ConflictError(
                f"Gebruiker '{username}' bestaat al.",
                code="USER_ALREADY_EXISTS",
                details={"username": username},
            )
        self._validate_password(password)

    def _validate_password(self, password: str) -> None:
        """Controleer de minimale wachtwoordlengte."""

        if len(password) < self.MINIMUM_PASSWORD_LENGTH:
            raise ValidationError(
                "Het wachtwoord moet minimaal 8 tekens bevatten.",
                code="PASSWORD_TOO_SHORT",
                details={"minimum_length": self.MINIMUM_PASSWORD_LENGTH},
            )
