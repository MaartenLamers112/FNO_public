"""Tests voor PhotoService."""

import pytest

from app.enums.author_type import AuthorType
from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Photo
from app.repositories import (
    CommentRepository,
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
    RoleRepository,
    UserRepository,
)
from app.services import PhotoService


def create_photo() -> Photo:
    """Maak een testfoto."""

    repository = PhotoRepository()

    photo = Photo(
        mm_id="MM-PHOTO-SERVICE",
        photo_number="A50001",
        publication_status=PublicationStatus.CONCEPT,
    )

    repository.add(photo)
    repository.save()

    return photo


def test_get_photo_by_id(app) -> None:
    """Een foto kan via het ID worden opgehaald."""

    photo = create_photo()

    service = PhotoService()

    stored_photo = service.get(photo.id)

    assert stored_photo is not None
    assert stored_photo.id == photo.id


def test_get_photo_by_mm_id(app) -> None:
    """Een foto kan via het MM-id worden opgehaald."""

    photo = create_photo()

    service = PhotoService()

    stored_photo = service.get_by_mm_id(photo.mm_id)

    assert stored_photo is not None
    assert stored_photo.id == photo.id


def test_get_photo_by_photo_number(app) -> None:
    """Een foto kan via het fotonummer worden opgehaald."""

    photo = create_photo()

    service = PhotoService()

    stored_photo = service.get_by_photo_number(photo.photo_number)

    assert stored_photo is not None
    assert stored_photo.id == photo.id


def test_unknown_photo_returns_none(app) -> None:
    """Onbekende foto's geven None terug."""

    service = PhotoService()

    assert service.get(999999) is None

    assert service.get_by_mm_id("UNKNOWN") is None

    assert service.get_by_photo_number("A99999") is None


def test_get_previous_photo(app) -> None:
    """De vorige foto kan worden opgehaald."""

    repository = PhotoRepository()

    first = repository.add(
        Photo(
            mm_id="MM001",
            photo_number="A00001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    middle = repository.add(
        Photo(
            mm_id="MM002",
            photo_number="A00002",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.add(
        Photo(
            mm_id="MM003",
            photo_number="A00003",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    service = PhotoService()

    previous = service.get_previous_photo(middle.id)

    assert previous is not None
    assert previous.id == first.id


def test_get_next_photo(app) -> None:
    """De volgende foto kan worden opgehaald."""

    repository = PhotoRepository()

    repository.add(
        Photo(
            mm_id="MM011",
            photo_number="A00011",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    middle = repository.add(
        Photo(
            mm_id="MM012",
            photo_number="A00012",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    last = repository.add(
        Photo(
            mm_id="MM013",
            photo_number="A00013",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    service = PhotoService()

    next_photo = service.get_next_photo(middle.id)

    assert next_photo is not None
    assert next_photo.id == last.id


def test_first_photo_has_no_previous(app) -> None:
    """De eerste foto heeft geen voorganger."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM021",
            photo_number="A00021",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    service = PhotoService()

    assert service.get_previous_photo(photo.id) is None


def test_last_photo_has_no_next(app) -> None:
    """De laatste foto heeft geen opvolger."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM031",
            photo_number="A00031",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    service = PhotoService()

    assert service.get_next_photo(photo.id) is None


def test_navigation_with_unknown_photo_returns_none(app) -> None:
    """Navigatie met een onbekend foto-ID geeft None terug."""

    service = PhotoService()

    assert service.get_previous_photo(999999) is None
    assert service.get_next_photo(999999) is None


def test_photo_can_be_published(app) -> None:
    """Een conceptfoto kan worden gepubliceerd."""

    photo = create_photo()
    service = PhotoService()

    published_photo = service.publish(photo.id)

    assert published_photo.publication_status == PublicationStatus.PUBLISHED

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1
    assert history[0].event_type == HistoryEventType.PHOTO_PUBLISHED
    assert history[0].old_value == "concept"
    assert history[0].new_value == "published"


def test_photo_can_be_hidden(app) -> None:
    """Een foto kan worden verborgen."""

    photo = create_photo()
    service = PhotoService()

    hidden_photo = service.hide(photo.id)

    assert hidden_photo.publication_status == PublicationStatus.HIDDEN

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1
    assert history[0].event_type == HistoryEventType.PHOTO_HIDDEN
    assert history[0].old_value == "concept"
    assert history[0].new_value == "hidden"


def test_photo_can_be_returned_to_concept(app) -> None:
    """Een gepubliceerde foto kan terug naar concept."""

    photo = create_photo()
    service = PhotoService()

    service.publish(photo.id)
    concept_photo = service.set_concept(photo.id)

    assert concept_photo.publication_status == PublicationStatus.CONCEPT

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 2
    assert history[0].event_type == HistoryEventType.PHOTO_CONCEPT
    assert history[0].old_value == "published"
    assert history[0].new_value == "concept"


def test_same_publication_status_creates_no_duplicate_history(app) -> None:
    """Dezelfde status opnieuw instellen maakt geen extra historie."""

    photo = create_photo()
    service = PhotoService()

    service.publish(photo.id)
    service.publish(photo.id)

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1


def test_publication_change_for_unknown_photo_fails(app) -> None:
    """Een statuswijziging vereist een bestaande foto."""

    service = PhotoService()

    with pytest.raises(NotFoundError) as exc:
        service.publish(999999)

    assert exc.value.code == "PHOTO_NOT_FOUND"
    assert exc.value.details == {
        "photo_id": 999999,
    }


def test_publication_history_records_user(app) -> None:
    """De uitvoerende gebruiker wordt in de historie opgeslagen."""

    role_repository = RoleRepository()
    user_repository = UserRepository()

    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    user = user_repository.create(
        username="publiceerder",
        password_hash="test-hash",
        role_id=role.id,
    )
    user_repository.save()

    photo = create_photo()
    service = PhotoService()

    service.publish(
        photo.id,
        user_id=user.id,
    )

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1
    assert history[0].user_id == user.id


def test_photo_service_counts_labels(app) -> None:
    """Het aantal labels op een foto wordt correct bepaald."""

    photo = create_photo()
    person_repository = PersonRepository()

    person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )
    person_repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.40,
        y_position=0.50,
    )
    person_repository.save()

    service = PhotoService()

    assert service.count_labels(photo.id) == 2
    assert service.has_labels(photo.id) is True


def test_photo_without_labels_reports_false(app) -> None:
    """Een foto zonder personen heeft nog geen labels."""

    photo = create_photo()
    service = PhotoService()

    assert service.count_labels(photo.id) == 0
    assert service.has_labels(photo.id) is False


def test_photo_service_counts_open_comments(app) -> None:
    """Alleen open, niet-verwijderde opmerkingen worden geteld."""

    photo = create_photo()
    comment_repository = CommentRepository()

    comment_repository.create(
        photo_id=photo.id,
        content="Eerste opmerking",
        author_type=AuthorType.VISITOR,
    )

    comment_repository.create(
        photo_id=photo.id,
        content="Tweede opmerking",
        author_type=AuthorType.VISITOR,
    )

    comment_repository.save()

    service = PhotoService()

    assert service.count_open_comments(photo.id) == 2


def test_photo_service_returns_summary(app) -> None:
    """Het compacte foto-overzicht bevat de benodigde waarden."""

    photo = create_photo()
    person_repository = PersonRepository()
    comment_repository = CommentRepository()

    person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
        current_name="Jan Peters",
    )
    person_repository.save()

    comment_repository.create(
        photo_id=photo.id,
        content="Controleer deze naam.",
        author_type=AuthorType.VISITOR,
    )
    comment_repository.save()

    service = PhotoService()

    summary = service.get_summary(photo.id)

    assert summary == {
        "id": photo.id,
        "mm_id": "MM-PHOTO-SERVICE",
        "photo_number": "A50001",
        "publication_status": "concept",
        "label_count": 1,
        "has_labels": True,
        "open_comment_count": 1,
    }


def test_photo_information_requires_existing_photo(app) -> None:
    """Tellingen en overzichten vereisen een bestaande foto."""

    service = PhotoService()

    methods = [
        service.count_labels,
        service.count_open_comments,
        service.has_labels,
        service.get_summary,
    ]

    for method in methods:
        with pytest.raises(NotFoundError) as exc:
            method(999999)

        assert exc.value.code == "PHOTO_NOT_FOUND"
        assert exc.value.details == {
            "photo_id": 999999,
        }


class FakeMemorixService:
    """Testdubbel voor de live MM-koppeling."""

    def get_photo_data(self, mm_id: str) -> dict[str, str]:
        """Geef voorspelbare testbrongegevens terug."""

        return {
            "image_source": f"https://images.example.test/{mm_id}.dzi",
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "",
        }


def test_photo_service_returns_detail_with_image_source(app) -> None:
    """Het fotodetail bevat de live afbeeldingsbron."""

    photo = create_photo()
    service = PhotoService(
        memorix_service=FakeMemorixService(),
    )

    detail = service.get_detail(photo.id)
    comparison = detail.pop("comparison")

    assert detail == {
        "id": photo.id,
        "mm_id": "MM-PHOTO-SERVICE",
        "photo_number": "A50001",
        "person_display_mode": "numbered",
        "person_display_count": 1,
        "label_size": 14,
        "publication_status": PublicationStatus.CONCEPT,
        "progress_status": "empty",
        "is_visible": False,
        "is_complete": False,
        "previous_photo_id": None,
        "next_photo_id": None,
        "image_source": "https://images.example.test/MM-PHOTO-SERVICE.dzi",
        "subject": "",
        "date": "",
        "location": "",
        "description": "",
    }
    assert comparison.status.value == "red"
    assert comparison.reliable is False
    assert all(field.status.value == "orange" for field in comparison.fields[:3])
    assert all(field.fno_value == "" for field in comparison.fields[:3])
    assert comparison.fields[3].status.value == "red"

    stored = PhotoRepository().get(photo.id)
    assert stored is not None
    assert stored.local_subject is None
    assert stored.local_date is None
    assert stored.local_location is None
    assert stored.local_description is None


def test_photo_service_reports_existing_fno_difference(app) -> None:
    """Bestaande FNO-data wordt behouden en als verschil gemarkeerd."""

    photo = create_photo()
    photo.local_subject = "Aangepaste groepsfoto"
    PhotoRepository().save()
    service = PhotoService(memorix_service=FakeMemorixService())

    detail = service.get_detail(photo.id)

    assert detail["subject"] == "Aangepaste groepsfoto"
    assert detail["comparison"].status.value == "red"
    subject = detail["comparison"].fields[0]
    assert subject.mm_value == "Groepsfoto"
    assert subject.fno_value == "Aangepaste groepsfoto"
    assert subject.equal is False


class LandingMemorixStub:
    """Vaste MM-brongegevens voor landingspaginatests."""

    def __init__(self, data: dict[str, dict[str, str]]) -> None:
        self.data = data

    def get_landing_data(self, mm_id: str) -> dict[str, str]:
        """Geef de ingestelde lijstgegevens terug."""

        return self.data[mm_id]


def test_landing_page_filters_and_sorts_live_metadata(app) -> None:
    """PhotoService zoekt, filtert en sorteert live lijstmetadata."""

    repository = PhotoRepository()
    repository.add(
        Photo(
            mm_id="MM-LANDING-001",
            photo_number="A70001",
            publication_status=PublicationStatus.PUBLISHED,
            local_subject="Schoolklas",
            local_date="1954",
            local_location="Vortum-Mullem",
        )
    )
    repository.add(
        Photo(
            mm_id="MM-LANDING-002",
            photo_number="A70002",
            publication_status=PublicationStatus.PUBLISHED,
            local_subject="Voetbalelftal",
            local_date="1962",
            local_location="Boxmeer",
        )
    )
    repository.save()

    service = PhotoService(
        repository=repository,
        memorix_service=LandingMemorixStub({
            "MM-LANDING-001": {
                "thumbnail_url": "https://example.test/1.jpg",
                "subject": "Schoolklas",
                "date": "1954",
                "location": "Vortum-Mullem",
            },
            "MM-LANDING-002": {
                "thumbnail_url": "https://example.test/2.jpg",
                "subject": "Voetbalelftal",
                "date": "1962",
                "location": "Boxmeer",
            },
        }),
    )

    result = service.get_landing_page(
        search="foto A700",
        location="Boxmeer",
        sort="date",
        direction="desc",
    )

    assert result["locations"] == ["Boxmeer", "Vortum-Mullem"]
    assert result["items"] == []

    result = service.get_landing_page(
        search="voetbal",
        location="Boxmeer",
        sort="date",
        direction="desc",
    )

    assert [item["photo_number"] for item in result["items"]] == ["A70002"]


class ImportMemorixStub:
    """Voorkom echte MM-aanroepen in importtests."""

    def get_photo_data(self, mm_id: str) -> dict[str, str]:
        """Geef een geldige afbeeldingsbron terug."""

        return {
            "image_source": "https://example.test/photo.dzi",
            "subject": "",
            "date": "",
            "location": "",
        }


def test_photo_can_be_imported_from_memorix(app) -> None:
    """Een geldig MM-record wordt als concept toegevoegd."""

    photo = PhotoService(
        memorix_service=ImportMemorixStub(),
    ).import_from_memorix(
        mm_id="MM-IMPORT-001",
        photo_number="I001",
    )

    assert photo.mm_id == "MM-IMPORT-001"
    assert photo.photo_number == "I001"
    assert photo.publication_status == PublicationStatus.CONCEPT

    history = HistoryRepository().get_by_photo(photo.id)
    assert history[0].event_type == HistoryEventType.PHOTO_IMPORTED


def test_duplicate_memorix_photo_is_rejected(app) -> None:
    """Hetzelfde MM-record kan niet tweemaal worden toegevoegd."""

    service = PhotoService(memorix_service=ImportMemorixStub())
    service.import_from_memorix(mm_id="MM-DUP", photo_number="D001")

    with pytest.raises(ConflictError) as exc:
        service.import_from_memorix(mm_id="MM-DUP", photo_number="D002")

    assert exc.value.code == "PHOTO_ALREADY_EXISTS"


class NamesListMemorixService:
    """MM-testdubbel met beschrijving en betrouwbare namenlijst."""

    def get_photo_data(self, mm_id: str) -> dict[str, str]:
        """Geef brongegevens met drie genummerde namen terug."""

        raw = "Beschrijving van de foto.\n\n1. Dien,\n2. Truus\n3. Mina"
        return {
            "image_source": f"https://images.example.test/{mm_id}.dzi",
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "Beschrijving van de foto. 1. Dien, 2. Truus 3. Mina",
            "description_raw": raw,
        }


def test_photo_service_compares_person_names_without_filling_them(app) -> None:
    """Een betrouwbare MM-lijst vergelijkt namen zonder FNO te wijzigen."""

    photo = create_photo()
    persons = PersonRepository()
    first = persons.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.1,
        y_position=0.1,
    )
    second = persons.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.2,
        y_position=0.2,
        current_name="Eigen FNO-naam",
    )
    persons.save()

    detail = PhotoService(memorix_service=NamesListMemorixService()).get_detail(
        photo.id
    )

    assert persons.get(first.id).current_name is None
    assert persons.get(second.id).current_name == "Eigen FNO-naam"
    comparisons = {item.label_number: item for item in detail["comparison"].persons}
    assert comparisons[1].status.value == "orange"
    assert comparisons[2].status.value == "orange"
    assert detail["description"] == ""


def test_person_display_mode_can_be_changed(app) -> None:
    """De servicelaag bewaart de gekozen personenweergave."""

    photo = create_photo()
    service = PhotoService()

    updated = service.update_person_display_mode(
        photo.id,
        person_display_mode="left_to_right",
        person_display_count=2,
    )

    assert updated.person_display_mode == "left_to_right"
    assert updated.person_display_count == 2
    history = HistoryRepository().get_by_photo(photo.id)

    assert any(
        event.event_type == HistoryEventType.PHOTO_PERSON_DISPLAY_MODE_CHANGED
        for event in history
    )


def test_invalid_person_display_mode_is_rejected(app) -> None:
    """Alleen de twee ondersteunde personenweergaven zijn geldig."""

    photo = create_photo()

    with pytest.raises(ValidationError) as exc:
        PhotoService().update_person_display_mode(
            photo.id,
            person_display_mode="unknown",
        )

    assert exc.value.code == "INVALID_PERSON_DISPLAY_MODE"


def test_photo_can_be_deleted_from_fno(app) -> None:
    """Verwijderen uit FNO verwijdert het lokale fotorecord."""

    photo = create_photo()
    service = PhotoService()

    service.delete_from_fno(photo.id)

    assert service.get(photo.id) is None


def test_opening_photo_does_not_implicitly_fill_local_metadata(app) -> None:
    """Live MM-weergave schrijft zonder expliciete aanvulactie niets naar FNO."""

    photo = create_photo()
    photo.local_subject = None
    photo.local_date = None
    photo.local_location = None
    photo.local_description = None
    PhotoRepository().save()

    service = PhotoService(memorix_service=FakeMemorixService())
    detail = service.get_detail(photo.id)

    assert detail["subject"] == ""
    assert detail["date"] == ""
    assert detail["location"] == ""
    assert detail["description"] == ""
    refreshed = PhotoRepository().get(photo.id)
    assert refreshed is not None
    assert refreshed.local_subject is None
    assert refreshed.local_date is None
    assert refreshed.local_location is None
    assert refreshed.local_description is None
