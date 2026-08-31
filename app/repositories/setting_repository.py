"""Repository voor functionele applicatie-instellingen."""

from __future__ import annotations

from sqlalchemy import select

from app.extensions import db
from app.models import Setting
from app.repositories.base_repository import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """Databasebewerkingen voor de Setting-entiteit."""

    model = Setting

    def get_by_key(self, key: str) -> Setting | None:
        """Haal een instelling op via de unieke sleutel."""

        statement = select(Setting).where(Setting.key == key)

        return db.session.scalar(statement)

    def exists_by_key(self, key: str) -> bool:
        """Controleer of een instelling met deze sleutel bestaat."""

        return self.exists_by(Setting.key, key)

    def create(
        self,
        *,
        key: str,
        value: str,
        description: str | None = None,
        updated_by_user_id: int | None = None,
    ) -> Setting:
        """Maak een nieuwe instelling aan."""

        setting = Setting(
            key=key,
            value=value,
            description=description,
            updated_by_user_id=updated_by_user_id,
        )

        return self.add(setting)

    def set_value(
        self,
        setting: Setting,
        *,
        value: str,
        updated_by_user_id: int | None = None,
    ) -> Setting:
        """Wijzig de waarde en de laatste beheerder."""

        setting.value = value
        setting.updated_by_user_id = updated_by_user_id

        return setting

    def update_description(
        self,
        setting: Setting,
        *,
        description: str | None,
    ) -> Setting:
        """Wijzig de beschrijving van een instelling."""

        setting.description = description

        return setting
