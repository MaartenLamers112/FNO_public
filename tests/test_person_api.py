"""Tests voor de REST API voor personen en fotolabels."""

import pytest

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.models import Person, Photo
from app.repositories import (
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
    RoleRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def login_employee(client, app) -> None:
    """Meld voor labelbeheer een medewerker aan."""

    role_repository = RoleRepository()
    role = role_repository.create(name="employee", description="Medewerker")
    role_repository.save()
    user_repository = UserRepository()
    user = user_repository.create(
        username="labelbeheerder",
        password_hash="tijdelijk",
        role_id=role.id,
    )
    user.set_password("test")
    user_repository.save()
    client.post(
        "/login",
        data={"username": "labelbeheerder", "password": "test"},
    )


def create_person() -> tuple[Photo, Person]:
    """Maak een foto met één persoonslabel."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()

    photo = photo_repository.add(
        Photo(
            mm_id="MM-PERSON-API",
            photo_number="A91001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    photo_repository.save()

    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )
    person_repository.save()

    return photo, person


def test_person_position_can_be_updated(client, app) -> None:
    """Een geldige PATCH-aanvraag verplaatst het label."""

    photo, person = create_person()

    response = client.patch(
        f"/api/persons/{person.id}/position",
        json={
            "x_position": 0.65,
            "y_position": 0.75,
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "id": person.id,
        "photo_id": photo.id,
        "label_number": 1,
        "x_position": 0.65,
        "y_position": 0.75,
        "current_name": "Jan Peters",
        "name_locked": False,
    }

    stored = PersonRepository().get(person.id)

    assert stored is not None
    assert stored.x_position == 0.65
    assert stored.y_position == 0.75

    moved_events = [
        item
        for item in HistoryRepository().get_by_photo(photo.id)
        if item.event_type == HistoryEventType.LABEL_MOVED
    ]

    assert len(moved_events) == 1


def test_unknown_person_position_returns_404(client) -> None:
    """Een onbekend label geeft HTTP 404."""

    response = client.patch(
        "/api/persons/999999/position",
        json={
            "x_position": 0.40,
            "y_position": 0.50,
        },
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "code": "PERSON_NOT_FOUND",
        "message": "Het label bestaat niet.",
        "details": {
            "person_id": 999999,
        },
    }


def test_position_outside_image_returns_400(client, app) -> None:
    """Coördinaten buiten nul en één worden geweigerd."""

    _, person = create_person()

    response = client.patch(
        f"/api/persons/{person.id}/position",
        json={
            "x_position": 1.10,
            "y_position": 0.50,
        },
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "code": "LABEL_X_POSITION_INVALID",
        "message": "De horizontale positie moet tussen 0 en 1 liggen.",
        "details": {
            "x_position": 1.10,
        },
    }


def test_missing_position_field_returns_400(client, app) -> None:
    """Een ontbrekend positieveld geeft een validatiefout."""

    _, person = create_person()

    response = client.patch(
        f"/api/persons/{person.id}/position",
        json={
            "x_position": 0.40,
        },
    )

    assert response.status_code == 400
    data = response.get_json()

    assert data["code"] == "REQUEST_VALIDATION_FAILED"
    assert data["message"] == "De aanvraag bevat ongeldige velden."
    assert data["details"]["errors"][0]["loc"] == ["y_position"]
    assert data["details"]["errors"][0]["type"] == "missing"


def test_invalid_json_body_returns_400(client, app) -> None:
    """Een ontbrekende JSON-body geeft een duidelijke fout."""

    _, person = create_person()

    response = client.patch(
        f"/api/persons/{person.id}/position",
        data="geen-json",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "code": "REQUEST_BODY_INVALID",
        "message": "De aanvraag bevat geen geldige JSON-body.",
        "details": {},
    }


def test_person_label_can_be_created(client, app) -> None:
    """Een POST-aanvraag maakt het volgende labelnummer aan."""

    photo, _ = create_person()

    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={
            "x_position": 0.45,
            "y_position": 0.55,
        },
    )

    assert response.status_code == 201
    data = response.get_json()

    assert data == {
        "id": data["id"],
        "photo_id": photo.id,
        "label_number": 2,
        "x_position": 0.45,
        "y_position": 0.55,
        "current_name": None,
        "name_locked": False,
    }

    created = PersonRepository().get(data["id"])
    assert created is not None

    created_events = [
        item
        for item in HistoryRepository().get_by_photo(photo.id)
        if item.event_type == HistoryEventType.LABEL_CREATED
    ]
    assert len(created_events) == 1
    assert created_events[0].person_id == created.id


def test_person_label_creation_uses_first_number_for_empty_photo(client, app) -> None:
    """De eerste persoon op een foto krijgt labelnummer één."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-EMPTY-PHOTO",
            photo_number="A91002",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={
            "x_position": 0.10,
            "y_position": 0.20,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["label_number"] == 1


def test_person_label_creation_rejects_position_outside_image(client, app) -> None:
    """Een nieuw label buiten de afbeelding wordt geweigerd."""

    photo, _ = create_person()

    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={
            "x_position": -0.01,
            "y_position": 0.50,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "LABEL_X_POSITION_INVALID"


def test_person_label_can_be_deleted(client, app) -> None:
    """Een DELETE-aanvraag verwijdert het label en schrijft historie."""

    photo, person = create_person()

    response = client.delete(f"/api/persons/{person.id}")

    assert response.status_code == 204
    assert PersonRepository().get(person.id) is None

    deleted_events = [
        item
        for item in HistoryRepository().get_by_photo(photo.id)
        if item.event_type == HistoryEventType.LABEL_DELETED
    ]

    assert len(deleted_events) == 1
    assert deleted_events[0].old_value == "1"


def test_deleting_label_resequences_remaining_labels(client, app) -> None:
    """Na verwijderen worden resterende labels opnieuw opeenvolgend genummerd."""

    photo, first = create_person()
    repository = PersonRepository()
    second = repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.40,
        y_position=0.50,
        current_name="Piet Janssen",
    )
    repository.save()

    response = client.delete(f"/api/persons/{first.id}")

    assert response.status_code == 204

    stored_second = repository.get(second.id)
    assert stored_second is not None
    assert stored_second.label_number == 1


def test_unknown_person_delete_returns_404(client) -> None:
    """Een onbekend label kan niet worden verwijderd."""

    response = client.delete("/api/persons/999999")

    assert response.status_code == 404
    assert response.get_json() == {
        "code": "PERSON_NOT_FOUND",
        "message": "Het label bestaat niet.",
        "details": {
            "person_id": 999999,
        },
    }


def test_update_person_name(client, app) -> None:
    """Een persoonsnaam kan via de API worden gewijzigd."""

    from app.extensions import db
    from app.models import Person, Photo

    with app.app_context():
        photo = Photo(mm_id="block-a-name", photo_number="A900", publication_status=0)
        db.session.add(photo)
        db.session.flush()
        person = Person(
            photo_id=photo.id, label_number=1, x_position=0.2, y_position=0.3
        )
        db.session.add(person)
        db.session.commit()
        person_id = person.id

    response = client.patch(
        f"/api/persons/{person_id}/name",
        json={"current_name": "Jan Jansen"},
    )

    assert response.status_code == 200
    assert response.get_json()["current_name"] == "Jan Jansen"


def test_update_person_number(client, app) -> None:
    """Een persoonslabel kan via de API worden hernummerd."""

    from app.extensions import db
    from app.models import Person, Photo

    with app.app_context():
        photo = Photo(mm_id="block-a-number", photo_number="A901", publication_status=0)
        db.session.add(photo)
        db.session.flush()
        first = Person(
            photo_id=photo.id, label_number=1, x_position=0.2, y_position=0.3
        )
        second = Person(
            photo_id=photo.id, label_number=2, x_position=0.4, y_position=0.5
        )
        db.session.add_all([first, second])
        db.session.commit()
        first_id = first.id

    response = client.patch(
        f"/api/persons/{first_id}/number",
        json={"label_number": 2},
    )

    assert response.status_code == 200
    assert response.get_json()["label_number"] == 2


def test_person_comment_can_be_deleted(client, app) -> None:
    """Een DELETE-aanvraag verwijdert een persoonsopmerking."""

    photo, person = create_person()
    create_response = client.post(
        f"/api/persons/{person.id}/comments",
        json={"content": "Deze opmerking mag weg."},
    )
    comment_id = create_response.get_json()["id"]

    response = client.delete(f"/api/persons/comments/{comment_id}")

    assert response.status_code == 204
    comments_response = client.get(f"/api/persons/{person.id}/comments")
    assert comments_response.get_json() == []

    deleted_events = [
        item
        for item in HistoryRepository().get_by_photo(photo.id)
        if item.event_type == HistoryEventType.COMMENT_DELETED
    ]
    assert len(deleted_events) == 1


def test_person_comment_text_can_be_autosaved(client, app) -> None:
    """De doorlopende opmerkingstekst kan in één aanvraag worden opgeslagen."""

    _, person = create_person()

    response = client.patch(
        f"/api/persons/{person.id}/comments-text",
        json={"content": "Eerste regel\nTweede gebruiker typt hieronder."},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "person_id": person.id,
        "content": "Eerste regel\nTweede gebruiker typt hieronder.",
        "has_comment": True,
    }

    comments = client.get(f"/api/persons/{person.id}/comments").get_json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Eerste regel\nTweede gebruiker typt hieronder."


def test_empty_person_comment_text_clears_comment(client, app) -> None:
    """Leegmaken van het veld verwijdert de doorlopende opmerkingstekst."""

    _, person = create_person()
    client.patch(
        f"/api/persons/{person.id}/comments-text",
        json={"content": "Wordt verwijderd"},
    )

    response = client.patch(
        f"/api/persons/{person.id}/comments-text",
        json={"content": ""},
    )

    assert response.status_code == 200
    assert response.get_json()["has_comment"] is False
    assert client.get(f"/api/persons/{person.id}/comments").get_json() == []
