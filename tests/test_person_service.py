"""Tests voor PersonService."""

import pytest

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.extensions import db
from app.models import Person, Photo
from app.repositories import HistoryRepository, PhotoRepository
from app.services import PersonService


def create_photo() -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM-PERSON-SERVICE",
            photo_number="A60001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    return photo


def test_person_service_requires_existing_photo(app) -> None:
    """Een label vereist een bestaande foto."""

    service = PersonService()

    with pytest.raises(NotFoundError) as exc:
        service.create_label(
            photo_id=999999,
            label_number=1,
            x_position=0.25,
            y_position=0.50,
        )

    assert exc.value.code == "PHOTO_NOT_FOUND"
    assert exc.value.details == {
        "photo_id": 999999,
    }


def test_person_service_can_create_label(app) -> None:
    """Een geldig label wordt opgeslagen."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
        current_name="  Jan Peters  ",
    )

    assert person.id is not None
    assert person.photo_id == photo.id
    assert person.label_number == 1
    assert person.x_position == 0.25
    assert person.y_position == 0.50
    assert person.current_name == "Jan Peters"


def test_create_label_writes_history(app) -> None:
    """Het aanmaken van een label schrijft een geschiedenisregel."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.40,
        y_position=0.60,
    )

    history = HistoryRepository().get_by_photo(photo.id)

    assert len(history) == 1
    assert history[0].person_id == person.id
    assert history[0].event_type == HistoryEventType.LABEL_CREATED
    assert history[0].description == "Label 3 toegevoegd"


def test_duplicate_label_number_is_rejected(app) -> None:
    """Een labelnummer moet binnen één foto uniek zijn."""

    photo = create_photo()
    service = PersonService()

    service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )

    with pytest.raises(ConflictError) as exc:
        service.create_label(
            photo_id=photo.id,
            label_number=1,
            x_position=0.60,
            y_position=0.70,
        )

    assert exc.value.code == "LABEL_NUMBER_ALREADY_EXISTS"
    assert exc.value.details == {
        "photo_id": photo.id,
        "label_number": 1,
    }


def test_invalid_label_number_is_rejected(app) -> None:
    """Labelnummers kleiner dan één worden geweigerd."""

    photo = create_photo()
    service = PersonService()

    with pytest.raises(ValidationError) as exc:
        service.create_label(
            photo_id=photo.id,
            label_number=0,
            x_position=0.25,
            y_position=0.50,
        )

    assert exc.value.code == "LABEL_NUMBER_INVALID"
    assert exc.value.details == {
        "label_number": 0,
    }


@pytest.mark.parametrize(
    ("x_position", "y_position", "expected_code"),
    [
        (-0.01, 0.50, "LABEL_X_POSITION_INVALID"),
        (1.01, 0.50, "LABEL_X_POSITION_INVALID"),
        (0.50, -0.01, "LABEL_Y_POSITION_INVALID"),
        (0.50, 1.01, "LABEL_Y_POSITION_INVALID"),
    ],
)
def test_invalid_label_position_is_rejected(
    app,
    x_position: float,
    y_position: float,
    expected_code: str,
) -> None:
    """Relatieve coördinaten moeten tussen nul en één liggen."""

    photo = create_photo()
    service = PersonService()

    with pytest.raises(ValidationError) as exc:
        service.create_label(
            photo_id=photo.id,
            label_number=1,
            x_position=x_position,
            y_position=y_position,
        )

    assert exc.value.code == expected_code


def test_blank_name_is_stored_as_none(app) -> None:
    """Een lege naam wordt niet als betekenisvolle naam opgeslagen."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
        current_name="   ",
    )

    assert person.current_name is None


def test_label_can_be_moved(app) -> None:
    """Een label kan worden verplaatst."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )

    moved = service.move_label(
        person_id=person.id,
        x_position=0.60,
        y_position=0.80,
    )

    assert moved.x_position == 0.60
    assert moved.y_position == 0.80


def test_move_unknown_label_fails(app) -> None:
    """Een onbekend label kan niet worden verplaatst."""

    service = PersonService()

    with pytest.raises(NotFoundError) as exc:
        service.move_label(
            person_id=999999,
            x_position=0.2,
            y_position=0.3,
        )

    assert exc.value.code == "PERSON_NOT_FOUND"


def test_new_label_number_must_be_within_range(app) -> None:
    """Een nieuw labelnummer moet binnen het bestaande bereik liggen."""

    photo = create_photo()
    service = PersonService()

    service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
    )

    with pytest.raises(ValidationError) as exc:
        service._validate_new_label_number(
            photo_id=photo.id,
            new_label_number=2,
        )

    assert exc.value.code == "LABEL_NUMBER_OUT_OF_RANGE"


def test_label_can_be_renumbered(app) -> None:
    """Een label kan worden hernummerd."""

    photo = create_photo()
    service = PersonService()

    first = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.1,
        y_position=0.1,
    )

    service.create_label(
        photo_id=photo.id,
        label_number=2,
        x_position=0.2,
        y_position=0.2,
    )

    service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.3,
        y_position=0.3,
    )

    service.renumber_label(
        person_id=first.id,
        new_label_number=3,
    )

    persons = service.repository.get_by_photo(photo.id)

    assert [person.label_number for person in persons] == [1, 2, 3]
    assert first.label_number == 3


def test_label_can_be_moved_up(app) -> None:
    """Een label kan omhoog worden verplaatst."""

    photo = create_photo()
    service = PersonService()

    service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.1,
        y_position=0.1,
        current_name="A",
    )

    service.create_label(
        photo_id=photo.id,
        label_number=2,
        x_position=0.2,
        y_position=0.2,
        current_name="B",
    )

    third = service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.3,
        y_position=0.3,
        current_name="C",
    )

    service.renumber_label(
        person_id=third.id,
        new_label_number=1,
    )

    persons = service.repository.get_by_photo(photo.id)

    assert [person.current_name for person in persons] == [
        "C",
        "A",
        "B",
    ]


def test_label_can_be_moved_down(app) -> None:
    """Een label kan omlaag worden verplaatst."""

    photo = create_photo()
    service = PersonService()

    first = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.1,
        y_position=0.1,
        current_name="A",
    )

    service.create_label(
        photo_id=photo.id,
        label_number=2,
        x_position=0.2,
        y_position=0.2,
        current_name="B",
    )

    service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.3,
        y_position=0.3,
        current_name="C",
    )

    service.renumber_label(
        person_id=first.id,
        new_label_number=3,
    )

    persons = service.repository.get_by_photo(photo.id)

    assert [person.current_name for person in persons] == [
        "B",
        "C",
        "A",
    ]


def test_renumber_to_same_number_does_nothing(app) -> None:
    """Een label hetzelfde nummer geven verandert niets."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
    )

    history_before = len(HistoryRepository().get_by_photo(photo.id))

    service.renumber_label(
        person_id=person.id,
        new_label_number=1,
    )

    history_after = len(HistoryRepository().get_by_photo(photo.id))

    assert history_before == history_after


def test_correct_person_receives_new_number(app) -> None:
    """Na hernummeren krijgt de juiste persoon het nieuwe nummer."""

    photo = create_photo()
    service = PersonService()

    service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.1,
        y_position=0.1,
        current_name="Jan",
    )

    second = service.create_label(
        photo_id=photo.id,
        label_number=2,
        x_position=0.2,
        y_position=0.2,
        current_name="Piet",
    )

    service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.3,
        y_position=0.3,
        current_name="Klaas",
    )

    service.renumber_label(
        person_id=second.id,
        new_label_number=3,
    )

    persons = service.repository.get_by_photo(photo.id)

    mapping = {person.current_name: person.label_number for person in persons}

    assert mapping == {
        "Jan": 1,
        "Klaas": 2,
        "Piet": 3,
    }


def test_person_name_can_be_changed(app) -> None:
    """De naam van een persoon kan worden gewijzigd."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
        current_name="Jan",
    )

    service.rename_person(
        person_id=person.id,
        new_name="Piet",
    )

    assert person.current_name == "Piet"


def test_person_name_is_trimmed(app) -> None:
    """Overbodige witruimte wordt verwijderd."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
    )

    service.rename_person(
        person_id=person.id,
        new_name="   Jan Peters   ",
    )

    assert person.current_name == "Jan Peters"


def test_blank_name_becomes_none(app) -> None:
    """Een lege naam wordt None."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
        current_name="Jan",
    )

    service.rename_person(
        person_id=person.id,
        new_name="     ",
    )

    assert person.current_name is None


def test_unknown_person_cannot_be_renamed(app) -> None:
    """Een onbekend label kan niet worden hernoemd."""

    service = PersonService()

    with pytest.raises(NotFoundError) as exc:
        service.rename_person(
            person_id=999999,
            new_name="Jan",
        )

    assert exc.value.code == "PERSON_NOT_FOUND"


def test_rename_to_same_name_does_nothing(app) -> None:
    """Een ongewijzigde naam schrijft geen historie."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
        current_name="Jan",
    )

    history_before = len(HistoryRepository().get_by_photo(photo.id))

    service.rename_person(
        person_id=person.id,
        new_name="Jan",
    )

    history_after = len(HistoryRepository().get_by_photo(photo.id))

    assert history_before == history_after


def test_label_can_be_deleted(app) -> None:
    """Een bestaand label kan worden verwijderd."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )

    service.delete_label(person_id=person.id)

    assert service.get(person.id) is None
    assert service.repository.get_by_photo(photo.id) == []


def test_deleting_label_resequences_remaining_labels(app) -> None:
    """Na verwijderen blijven de labelnummers opeenvolgend."""

    photo = create_photo()
    service = PersonService()

    first = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.10,
        y_position=0.10,
        current_name="A",
    )

    second = service.create_label(
        photo_id=photo.id,
        label_number=2,
        x_position=0.20,
        y_position=0.20,
        current_name="B",
    )

    third = service.create_label(
        photo_id=photo.id,
        label_number=3,
        x_position=0.30,
        y_position=0.30,
        current_name="C",
    )

    service.delete_label(person_id=second.id)

    persons = service.repository.get_by_photo(photo.id)

    assert [person.current_name for person in persons] == [
        "A",
        "C",
    ]
    assert [person.label_number for person in persons] == [
        1,
        2,
    ]
    assert first.label_number == 1
    assert third.label_number == 2


def test_deleting_last_label_needs_no_resequencing(app) -> None:
    """Ook het laatste label van een foto kan worden verwijderd."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )

    service.delete_label(person_id=person.id)

    assert service.repository.get_by_photo(photo.id) == []


def test_deleting_unknown_label_fails(app) -> None:
    """Een onbekend label kan niet worden verwijderd."""

    service = PersonService()

    with pytest.raises(NotFoundError) as exc:
        service.delete_label(person_id=999999)

    assert exc.value.code == "PERSON_NOT_FOUND"
    assert exc.value.details == {
        "person_id": 999999,
    }


def test_deleting_label_writes_history(app) -> None:
    """Verwijderen schrijft een auditregel met het oude labelnummer."""

    photo = create_photo()
    service = PersonService()

    person = service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )

    service.delete_label(person_id=person.id)

    history = HistoryRepository().get_by_photo(photo.id)

    deleted_events = [
        item for item in history if item.event_type == HistoryEventType.LABEL_DELETED
    ]

    assert len(deleted_events) == 1
    assert deleted_events[0].person_id is None
    assert deleted_events[0].old_value == "1"
    assert deleted_events[0].new_value is None
    assert deleted_events[0].description == ("Label 1 verwijderd (Jan Peters)")


def test_next_label_number_is_determined_by_backend(app) -> None:
    """De service bepaalt het eerstvolgende labelnummer."""

    photo = create_photo()
    service = PersonService()

    service.create_label(
        photo_id=photo.id,
        label_number=1,
        x_position=0.10,
        y_position=0.20,
    )

    person = service.create_next_label(
        photo_id=photo.id,
        x_position=0.30,
        y_position=0.40,
    )

    assert person.label_number == 2
    assert person.x_position == 0.30
    assert person.y_position == 0.40


def test_create_labels_from_detections(app) -> None:
    """Automatisch gedetecteerde labels worden opeenvolgend opgeslagen."""

    with app.app_context():
        photo = Photo(mm_id="mm-ai-apply", photo_number="AI1")
        db.session.add(photo)
        db.session.commit()

        persons = PersonService().create_labels_from_detections(
            photo_id=photo.id,
            positions=[(0.2, 0.3), (0.7, 0.4)],
        )

        assert [person.label_number for person in persons] == [1, 2]
        assert [person.x_position for person in persons] == [0.2, 0.7]


def test_renumber_by_position_uses_rows_and_left_to_right(app) -> None:
    """Automatisch hernummeren volgt de visuele leesvolgorde."""

    with app.app_context():
        photo = Photo(mm_id="MM-RENUMBER", photo_number="R-1")
        db.session.add(photo)
        db.session.flush()
        people = [
            Person(photo_id=photo.id, label_number=1, x_position=0.80, y_position=0.20),
            Person(photo_id=photo.id, label_number=2, x_position=0.20, y_position=0.22),
            Person(photo_id=photo.id, label_number=3, x_position=0.50, y_position=0.50),
        ]
        db.session.add_all(people)
        db.session.commit()

        result = PersonService().renumber_by_position(photo_id=photo.id)

        assert [person.id for person in result] == [
            people[1].id,
            people[0].id,
            people[2].id,
        ]
        assert [person.label_number for person in result] == [1, 2, 3]
