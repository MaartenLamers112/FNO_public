"""Tests voor HistoryRepository."""

from datetime import UTC, datetime, timedelta

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import (
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
    RoleRepository,
    UserRepository,
)


def create_photo() -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()

    photo = Photo(
        mm_id="MM-HISTORY-001",
        photo_number="A30001",
        publication_status=PublicationStatus.CONCEPT,
    )

    repository.add(photo)
    repository.save()

    return photo


def create_user() -> int:
    """Maak een testgebruiker aan en geef de ID terug."""

    role_repository = RoleRepository()
    user_repository = UserRepository()

    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    user = user_repository.create(
        username="medewerker",
        password_hash="test-hash",
        role_id=role.id,
    )
    user_repository.save()

    return user.id


def test_history_repository_can_create_history(app) -> None:
    """Een geschiedenisregel kan worden opgeslagen."""

    photo = create_photo()
    repository = HistoryRepository()

    history = repository.create(
        photo_id=photo.id,
        event_type=HistoryEventType.PHOTO_PUBLISHED,
        description="Foto gepubliceerd",
        old_value="concept",
        new_value="published",
    )
    repository.save()

    stored_history = repository.get(history.id)

    assert stored_history is not None
    assert stored_history.photo_id == photo.id
    assert stored_history.event_type == HistoryEventType.PHOTO_PUBLISHED
    assert stored_history.old_value == "concept"
    assert stored_history.new_value == "published"


def test_history_repository_can_get_by_photo(app) -> None:
    """Historie kan per foto worden opgehaald."""

    photo = create_photo()
    repository = HistoryRepository()

    repository.create(
        photo_id=photo.id,
        event_type=HistoryEventType.PHOTO_CONCEPT,
        description="Foto als concept toegevoegd",
    )
    repository.create(
        photo_id=photo.id,
        event_type=HistoryEventType.PHOTO_PUBLISHED,
        description="Foto gepubliceerd",
    )
    repository.save()

    history = repository.get_by_photo(photo.id)

    assert len(history) == 2
    assert repository.count_by_photo(photo.id) == 2


def test_history_repository_can_get_by_person(app) -> None:
    """Historie kan per persoon worden opgehaald."""

    photo = create_photo()
    person_repository = PersonRepository()
    history_repository = HistoryRepository()

    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
    )
    person_repository.save()

    history_repository.create(
        photo_id=photo.id,
        person_id=person.id,
        event_type=HistoryEventType.LABEL_MOVED,
        description="Label 1 verplaatst",
        old_value="0.25,0.50",
        new_value="0.40,0.60",
    )
    history_repository.save()

    history = history_repository.get_by_person(person.id)

    assert len(history) == 1
    assert history[0].person_id == person.id


def test_history_repository_can_get_by_user(app) -> None:
    """Historie kan per uitvoerende gebruiker worden opgehaald."""

    photo = create_photo()
    user_id = create_user()
    repository = HistoryRepository()

    repository.create(
        photo_id=photo.id,
        user_id=user_id,
        event_type=HistoryEventType.PHOTO_HIDDEN,
        description="Foto verborgen",
    )
    repository.save()

    history = repository.get_by_user(user_id)

    assert len(history) == 1
    assert history[0].user_id == user_id


def test_history_repository_limits_recent_results(app) -> None:
    """De recente selectie respecteert de opgegeven limiet."""

    photo = create_photo()
    repository = HistoryRepository()

    for number in range(5):
        repository.create(
            photo_id=photo.id,
            event_type=HistoryEventType.LABEL_CREATED,
            description=f"Label {number + 1} toegevoegd",
        )

    repository.save()

    recent_history = repository.get_recent(limit=3)

    assert len(recent_history) == 3


def test_history_repository_can_filter_by_period(app) -> None:
    """Historie kan binnen een tijdvak worden geselecteerd."""

    photo = create_photo()
    repository = HistoryRepository()

    history = repository.create(
        photo_id=photo.id,
        event_type=HistoryEventType.NAME_CHANGED,
        description="Naam gewijzigd",
        old_value="Jan",
        new_value="Jan Peters",
    )
    repository.save()

    assert history.created_at is not None

    start = history.created_at.replace(tzinfo=UTC) - timedelta(minutes=1)

    end = history.created_at.replace(tzinfo=UTC) + timedelta(minutes=1)

    results = repository.get_created_between(
        started_at=start,
        ended_at=end,
    )

    assert len(results) == 1
    assert results[0].id == history.id


def test_history_repository_uses_naive_utc_for_periods(app) -> None:
    """Ook tijdzonebewuste invoer wordt naar naïeve UTC geconverteerd."""

    photo = create_photo()
    repository = HistoryRepository()

    repository.create(
        photo_id=photo.id,
        event_type=HistoryEventType.SYNCHRONIZATION_COMPLETED,
        description="Synchronisatie voltooid",
    )
    repository.save()

    start = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )
    end = datetime(
        2027,
        1,
        1,
        tzinfo=UTC,
    )

    results = repository.get_created_between(
        started_at=start,
        ended_at=end,
    )

    assert len(results) == 1
