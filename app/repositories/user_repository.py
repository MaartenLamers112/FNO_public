"""Repository voor geauthenticeerde FNO-gebruikers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models import User
from app.models.mixins import normalize_utc, utc_now
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Databasebewerkingen voor de User-entiteit."""

    model = User

    def get_by_username(self, username: str) -> User | None:
        """Haal een gebruiker op via de unieke gebruikersnaam."""

        statement = select(User).where(User.username == username)

        return db.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        """Haal een gebruiker op via het unieke e-mailadres."""

        statement = select(User).where(User.email == email)

        return db.session.scalar(statement)

    def exists_by_username(self, username: str) -> bool:
        """Controleer of een gebruikersnaam al bestaat."""

        return self.exists_by(User.username, username)

    def exists_by_email(self, email: str) -> bool:
        """Controleer of een e-mailadres al bestaat."""

        return self.exists_by(User.email, email)

    def create(
        self,
        *,
        username: str,
        password_hash: str,
        role_id: int,
        email: str | None = None,
        email_verified: bool = False,
        is_active: bool = True,
    ) -> User:
        """Maak een gebruiker aan en voeg deze toe aan de sessie."""

        user = User(
            username=username,
            email=email,
            email_verified=email_verified,
            password_hash=password_hash,
            role_id=role_id,
            is_active=is_active,
        )

        return self.add(user)

    def update(
        self,
        user: User,
        *,
        username: str | None = None,
        role_id: int | None = None,
        is_active: bool | None = None,
        password_hash: str | None = None,
    ) -> User:
        """Werk de opgegeven gebruikersvelden bij."""

        if username is not None:
            user.username = username

        if role_id is not None:
            user.role_id = role_id

        if is_active is not None:
            user.is_active = is_active

        if password_hash is not None:
            user.password_hash = password_hash

        return user

    def update_email(
        self,
        user: User,
        *,
        email: str,
        verified: bool,
    ) -> User:
        """Werk e-mailadres en verificatiestatus samen bij."""

        user.email = email
        user.email_verified = verified
        return user

    def set_email_verified(self, user: User, *, verified: bool) -> User:
        """Werk de e-mailverificatiestatus bij."""

        user.email_verified = verified
        return user

    def update_last_login(
        self,
        user: User,
        logged_in_at: datetime | None = None,
    ) -> User:
        """Registreer het laatste succesvolle loginmoment in UTC."""

        user.last_login = (
            normalize_utc(logged_in_at) if logged_in_at is not None else utc_now()
        )

        return user

    def has_references(self, user: User) -> bool:
        """Controleer of een gebruiker nog door applicatiedata wordt gebruikt."""

        return any((
            user.history,
            user.name_changes,
            user.metadata_changes,
            user.comments,
            user.closed_comments,
            user.deleted_comments,
            user.updated_settings,
            user.role_upgrade_requests,
            user.reviewed_role_upgrade_requests,
        ))
