"""Tests voor HistoryService."""

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import HistoryRepository, PhotoRepository
from app.services import HistoryService


def create_photo() -> Photo:
    """Maak een testfoto."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM-HISTORY",
            photo_number="A70001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    return photo


def test_history_service_can_record_event(app) -> None:
    """Een historie-item kan worden geregistreerd."""

    photo = create_photo()

    service = HistoryService()

    service.record(
        photo_id=photo.id,
        event_type=HistoryEventType.PHOTO_PUBLISHED,
        description="Foto gepubliceerd",
        old_value="concept",
        new_value="published",
    )

    service.repository.save()

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1
    assert history[0].event_type == HistoryEventType.PHOTO_PUBLISHED
    assert history[0].old_value == "concept"
    assert history[0].new_value == "published"
