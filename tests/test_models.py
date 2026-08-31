"""Integratietests voor de SQLAlchemy-modellen."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.enums.publication_status import PublicationStatus
from app.extensions import db
from app.models import Person, Photo, Role, User


def test_role_user_photo_and_person_can_be_saved(app) -> None:
    """De belangrijkste modellen en relaties kunnen worden opgeslagen."""

    role = Role(
        name="administrator",
        description="Beheerder",
    )

    user = User(
        username="beheer",
        role=role,
    )
    user.set_password("veilig-testwachtwoord")

    photo = Photo(
        mm_id="test-mm-id-001",
        photo_number="A00001",
        publication_status=PublicationStatus.CONCEPT,
    )

    person = Person(
        photo=photo,
        label_number=1,
        x_position=0.25,
        y_position=0.75,
        current_name="Jan Peters",
    )

    db.session.add_all([role, user, photo, person])
    db.session.commit()

    assert role.id is not None
    assert user.id is not None
    assert photo.id is not None
    assert person.id is not None

    assert user.role is role
    assert person.photo is photo
    assert photo.persons == [person]

    assert user.check_password("veilig-testwachtwoord")
    assert not user.check_password("verkeerd-wachtwoord")


def test_label_number_must_be_unique_within_photo(app) -> None:
    """Eén labelnummer mag per foto maar eenmaal voorkomen."""

    photo = Photo(
        mm_id="test-mm-id-002",
        photo_number="A00002",
        publication_status=PublicationStatus.CONCEPT,
    )

    first_person = Person(
        photo=photo,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
    )

    second_person = Person(
        photo=photo,
        label_number=1,
        x_position=0.60,
        y_position=0.70,
    )

    db.session.add_all([photo, first_person, second_person])

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_person_requires_existing_photo(app) -> None:
    """Een persoon kan niet naar een niet-bestaande foto verwijzen."""

    person = Person(
        photo_id=999999,
        label_number=1,
        x_position=0.50,
        y_position=0.50,
    )

    db.session.add(person)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()


def test_deleting_photo_deletes_its_persons(app) -> None:
    """Personen verdwijnen wanneer hun bijbehorende foto wordt verwijderd."""

    photo = Photo(
        mm_id="test-mm-id-003",
        photo_number="A00003",
        publication_status=PublicationStatus.CONCEPT,
    )

    person = Person(
        photo=photo,
        label_number=1,
        x_position=0.40,
        y_position=0.60,
    )

    db.session.add(photo)
    db.session.commit()

    person_id = person.id

    db.session.delete(photo)
    db.session.commit()

    assert db.session.get(Person, person_id) is None


def test_photo_defaults_to_numbered_person_display(app) -> None:
    """Nieuwe foto's gebruiken standaard genummerde personenweergave."""

    photo = Photo(
        mm_id="test-mm-display-mode",
        photo_number="A00999",
        publication_status=PublicationStatus.CONCEPT,
    )
    db.session.add(photo)
    db.session.commit()

    assert photo.person_display_mode == "numbered"
