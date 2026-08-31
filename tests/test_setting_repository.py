"""Tests voor SettingRepository."""

from app.repositories import (
    RoleRepository,
    SettingRepository,
    UserRepository,
)


def create_user() -> int:
    """Maak een beheerder aan en geef de gebruikers-ID terug."""

    role_repository = RoleRepository()
    user_repository = UserRepository()

    role = role_repository.create(
        name="administrator",
        description="Beheerder",
    )
    role_repository.save()

    user = user_repository.create(
        username="beheer",
        password_hash="test-hash",
        role_id=role.id,
    )
    user_repository.save()

    return user.id


def test_setting_repository_can_create_and_find_setting(app) -> None:
    """Een instelling kan worden aangemaakt en via de sleutel gevonden."""

    repository = SettingRepository()

    setting = repository.create(
        key="organization_name",
        value="Stichting De Oude Schoenendoos",
        description="Naam van de organisatie",
    )
    repository.save()

    stored_setting = repository.get_by_key("organization_name")

    assert stored_setting is not None
    assert stored_setting.id == setting.id
    assert stored_setting.value == "Stichting De Oude Schoenendoos"
    assert stored_setting.description == "Naam van de organisatie"


def test_setting_repository_reports_existing_key(app) -> None:
    """De repository herkent een reeds gebruikte sleutel."""

    repository = SettingRepository()

    repository.create(
        key="default_language",
        value="nl",
    )
    repository.save()

    assert repository.exists_by_key("default_language")
    assert not repository.exists_by_key("unknown_setting")


def test_setting_repository_can_update_value(app) -> None:
    """De waarde van een instelling kan worden gewijzigd."""

    repository = SettingRepository()

    setting = repository.create(
        key="thumbnail_size",
        value="medium",
    )
    repository.save()

    repository.set_value(
        setting,
        value="large",
    )
    repository.save()

    stored_setting = repository.get(setting.id)

    assert stored_setting is not None
    assert stored_setting.value == "large"


def test_setting_repository_records_updating_user(app) -> None:
    """De beheerder die de instelling wijzigde wordt vastgelegd."""

    user_id = create_user()
    repository = SettingRepository()

    setting = repository.create(
        key="maintenance_mode",
        value="false",
    )
    repository.save()

    repository.set_value(
        setting,
        value="true",
        updated_by_user_id=user_id,
    )
    repository.save()

    stored_setting = repository.get(setting.id)

    assert stored_setting is not None
    assert stored_setting.updated_by_user_id == user_id


def test_setting_repository_can_update_description(app) -> None:
    """De beschrijving van een instelling kan worden gewijzigd."""

    repository = SettingRepository()

    setting = repository.create(
        key="synchronization_interval",
        value="60",
        description="Oude beschrijving",
    )
    repository.save()

    repository.update_description(
        setting,
        description="Synchronisatie-interval in minuten",
    )
    repository.save()

    stored_setting = repository.get(setting.id)

    assert stored_setting is not None
    assert stored_setting.description == "Synchronisatie-interval in minuten"


def test_setting_repository_can_delete_setting(app) -> None:
    """Een instelling kan worden verwijderd."""

    repository = SettingRepository()

    setting = repository.create(
        key="temporary_setting",
        value="test",
    )
    repository.save()

    setting_id = setting.id

    repository.delete(setting)
    repository.save()

    assert repository.get(setting_id) is None
