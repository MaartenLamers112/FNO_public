"""Tests voor PersonRepository."""

from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import PersonRepository, PhotoRepository


def create_photo(
    mm_id: str = "MM-PERSON-001",
    photo_number: str = "A10001",
) -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()

    photo = Photo(
        mm_id=mm_id,
        photo_number=photo_number,
        publication_status=PublicationStatus.CONCEPT,
    )

    repository.add(photo)
    repository.save()

    return photo


def test_person_repository_can_create_and_get_by_photo(app) -> None:
    """Personen worden op labelnummer teruggegeven."""

    photo = create_photo()
    repository = PersonRepository()

    repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.40,
        y_position=0.50,
        current_name="Piet Jansen",
    )
    repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )
    repository.save()

    persons = repository.get_by_photo(photo.id)

    assert [person.label_number for person in persons] == [1, 2]


def test_person_repository_can_find_by_number(app) -> None:
    """Een persoon kan op foto en labelnummer worden gevonden."""

    photo = create_photo()
    repository = PersonRepository()

    person = repository.create(
        photo_id=photo.id,
        label_number=7,
        x_position=0.25,
        y_position=0.75,
    )
    repository.save()

    stored_person = repository.find_by_number(
        photo.id,
        7,
    )

    assert stored_person is not None
    assert stored_person.id == person.id


def test_person_repository_can_find_by_partial_name(app) -> None:
    """Zoeken op naam is gedeeltelijk en niet hoofdlettergevoelig."""

    photo = create_photo()
    repository = PersonRepository()

    repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )
    repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.40,
        y_position=0.50,
        current_name="Maria Janssen",
    )
    repository.save()

    persons = repository.find_by_name("PETERS")

    assert len(persons) == 1
    assert persons[0].current_name == "Jan Peters"


def test_person_repository_detects_existing_label_number(app) -> None:
    """Een bestaand labelnummer binnen dezelfde foto wordt herkend."""

    photo = create_photo()
    repository = PersonRepository()

    person = repository.create(
        photo_id=photo.id,
        label_number=3,
        x_position=0.30,
        y_position=0.40,
    )
    repository.save()

    assert repository.exists_label_number(photo.id, 3)
    assert not repository.exists_label_number(photo.id, 4)

    assert not repository.exists_label_number(
        photo.id,
        3,
        exclude_person_id=person.id,
    )


def test_person_repository_can_move_and_renumber_person(app) -> None:
    """Positie en labelnummer kunnen worden gewijzigd."""

    photo = create_photo()
    repository = PersonRepository()

    person = repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )
    repository.save()

    repository.move(
        person,
        x_position=0.60,
        y_position=0.70,
    )
    repository.renumber(
        person,
        label_number=5,
    )
    repository.save()

    stored_person = repository.get(person.id)

    assert stored_person is not None
    assert stored_person.label_number == 5
    assert stored_person.x_position == 0.60
    assert stored_person.y_position == 0.70


def test_person_repository_can_update_name(app) -> None:
    """De actuele naam kan worden gewijzigd of leeggemaakt."""

    photo = create_photo()
    repository = PersonRepository()

    person = repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )
    repository.save()

    repository.update(
        person,
        current_name="Berta Jansen – Pieters",
    )
    repository.save()

    stored_person = repository.get(person.id)

    assert stored_person is not None
    assert stored_person.current_name == "Berta Jansen – Pieters"
