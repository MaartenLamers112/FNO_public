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

    def exists_by_username(self, username: str) -> bool:
        """Controleer of een gebruikersnaam al bestaat."""

        return self.exists_by(User.username, username)

    def create(
        self,
        *,
        username: str,
        password_hash: str,
        role_id: int,
        is_active: bool = True,
    ) -> User:
        """Maak een gebruiker aan en voeg deze toe aan de sessie."""

        user = User(
            username=username,
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
