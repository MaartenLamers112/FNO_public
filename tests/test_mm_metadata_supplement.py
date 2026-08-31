"""Tests voor veilig aanvullen van FNO-metadata vanuit MM."""

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import HistoryRepository, PhotoRepository
from app.services import MemorixService, MmImportService


def mm_record(
    *,
    mm_id: str,
    photo_number: str,
    subject: str = "MM onderwerp",
    date: str = "1954",
    location: str = "Vortum-Mullem",
    description: str = "MM beschrijving",
) -> dict[str, object]:
    """Maak een representatief MM-zoekrecord."""

    return {
        "fields": {
            "delving_hubId": [mm_id],
            "dc_identifier": [photo_number],
            "dc_title": [subject],
            "dcterms_created": [date],
            "tib_place": [location],
            "dc_description": [description],
        }
    }


def test_metadata_normalization_is_centralized(app) -> None:
    """MM-velden worden via één normalisatiemethode naar FNO vertaald."""

    with app.app_context():
        metadata = MemorixService().normalize_metadata_from_fields(
            mm_record(mm_id="MM-001", photo_number="A001")["fields"]
        )

    assert metadata.subject == "MM onderwerp"
    assert metadata.date == "1954"
    assert metadata.location == "Vortum-Mullem"
    assert metadata.description == "MM beschrijving"
    assert metadata.as_local_values() == {
        "subject": "MM onderwerp",
        "date": "1954",
        "location": "Vortum-Mullem",
        "description": "MM beschrijving",
    }


def test_supplement_only_fills_empty_local_fields(app) -> None:
    """Aanvullen vanuit MM overschrijft nooit bestaande FNO-inhoud."""

    with app.app_context():
        repository = PhotoRepository()
        photo = repository.add(
            Photo(
                mm_id="MM-001",
                photo_number="A001",
                publication_status=PublicationStatus.CONCEPT,
                local_subject="Eigen FNO onderwerp",
                local_date=None,
                local_location="   ",
                local_description="Eigen FNO beschrijving",
            )
        )
        repository.save()

        class FakeMemorixService(MemorixService):
            def get_metadata_record(self, mm_id: str):
                assert mm_id == "MM-001"
                fields = mm_record(mm_id=mm_id, photo_number="A001")["fields"]
                return fields, self.normalize_metadata_from_fields(fields)

        result = MmImportService(
            photo_repository=repository,
            memorix_service=FakeMemorixService(),
        ).supplement_missing_metadata(user_id=None)

        refreshed = repository.get(photo.id)
        assert refreshed is not None
        assert refreshed.local_subject == "Eigen FNO onderwerp"
        assert refreshed.local_date == "1954"
        assert refreshed.local_location == "Vortum-Mullem"
        assert refreshed.local_description == "Eigen FNO beschrijving"
        assert result.checked_photos == 1
        assert result.matched_photos == 1
        assert result.updated_photos == 1
        assert result.updated_fields == 2
        assert result.missing_photos == 0

        events = HistoryRepository().get_by_photo(photo.id)
        supplement_events = [
            event
            for event in events
            if event.event_type == HistoryEventType.METADATA_CHANGED
        ]
        assert len(supplement_events) == 2
        assert {event.new_value for event in supplement_events} == {
            "1954",
            "Vortum-Mullem",
        }


def test_supplement_is_idempotent(app) -> None:
    """Herhaald aanvullen verandert reeds gevulde FNO-data niet opnieuw."""

    with app.app_context():
        repository = PhotoRepository()
        photo = repository.add(
            Photo(
                mm_id="MM-002",
                photo_number="A002",
                publication_status=PublicationStatus.CONCEPT,
            )
        )
        repository.save()

        class FakeMemorixService(MemorixService):
            def get_metadata_record(self, mm_id: str):
                fields = mm_record(mm_id=mm_id, photo_number="A002")["fields"]
                return fields, self.normalize_metadata_from_fields(fields)

        service = MmImportService(
            photo_repository=repository,
            memorix_service=FakeMemorixService(),
        )
        first = service.supplement_missing_metadata(user_id=None)
        second = service.supplement_missing_metadata(user_id=None)

        assert first.updated_fields == 4
        assert second.updated_fields == 0
        assert second.updated_photos == 0
        events = HistoryRepository().get_by_photo(photo.id)
        assert (
            sum(
                event.event_type == HistoryEventType.METADATA_CHANGED
                for event in events
            )
            == 4
        )


def test_supplement_reports_photos_missing_from_mm_search(app) -> None:
    """Niet teruggevonden MM-records worden alleen gerapporteerd."""

    with app.app_context():
        repository = PhotoRepository()
        repository.add(
            Photo(
                mm_id="MM-MISSING",
                photo_number="A003",
                publication_status=PublicationStatus.CONCEPT,
            )
        )
        repository.save()

        class EmptyMemorixService(MemorixService):
            def get_metadata_record(self, mm_id: str):
                from app.exceptions import NotFoundError

                raise NotFoundError(
                    "Het Maior Memorix-record bestaat niet.",
                    code="MEMORIX_RECORD_NOT_FOUND",
                    details={"mm_id": mm_id},
                )

        result = MmImportService(
            photo_repository=repository,
            memorix_service=EmptyMemorixService(),
        ).supplement_missing_metadata(user_id=None)

        assert result.checked_photos == 1
        assert result.matched_photos == 0
        assert result.updated_fields == 0
        assert result.missing_photos == 1


def test_supplement_only_requests_photos_with_missing_metadata(app) -> None:
    """Alleen foto's met lege lokale metadata worden gericht uit MM opgehaald."""

    with app.app_context():
        repository = PhotoRepository()
        repository.add(
            Photo(
                mm_id="MM-COMPLETE",
                photo_number="A004",
                publication_status=PublicationStatus.CONCEPT,
                local_subject="FNO onderwerp",
                local_date="1954",
                local_location="Vortum-Mullem",
                local_description="FNO beschrijving",
            )
        )
        repository.add(
            Photo(
                mm_id="MM-INCOMPLETE",
                photo_number="A005",
                publication_status=PublicationStatus.CONCEPT,
                local_subject="FNO onderwerp",
                local_date=None,
                local_location="Vortum-Mullem",
                local_description="FNO beschrijving",
            )
        )
        repository.save()

        class CountingMemorixService(MemorixService):
            requested_ids: list[str] = []

            def get_metadata_record(self, mm_id: str):
                self.requested_ids.append(mm_id)
                fields = mm_record(mm_id=mm_id, photo_number="A005")["fields"]
                return fields, self.normalize_metadata_from_fields(fields)

        memorix_service = CountingMemorixService()
        result = MmImportService(
            photo_repository=repository,
            memorix_service=memorix_service,
        ).supplement_missing_metadata(user_id=None)

        assert memorix_service.requested_ids == ["MM-INCOMPLETE"]
        assert result.checked_photos == 2
        assert result.matched_photos == 1
        assert result.updated_photos == 1
        assert result.updated_fields == 1
        assert result.missing_photos == 0


def test_supplement_skips_mm_when_all_local_metadata_is_filled(app) -> None:
    """Volledig gevulde FNO-foto's veroorzaken geen MM-opvraag."""

    with app.app_context():
        repository = PhotoRepository()
        repository.add(
            Photo(
                mm_id="MM-COMPLETE",
                photo_number="A006",
                publication_status=PublicationStatus.CONCEPT,
                local_subject="FNO onderwerp",
                local_date="1954",
                local_location="Vortum-Mullem",
                local_description="FNO beschrijving",
            )
        )
        repository.save()

        class UnexpectedMemorixService(MemorixService):
            def get_metadata_record(self, mm_id: str):
                raise AssertionError("MM mag niet worden opgevraagd")

        result = MmImportService(
            photo_repository=repository,
            memorix_service=UnexpectedMemorixService(),
        ).supplement_missing_metadata(user_id=None)

        assert result.checked_photos == 1
        assert result.matched_photos == 0
        assert result.updated_photos == 0
        assert result.updated_fields == 0
        assert result.missing_photos == 0
