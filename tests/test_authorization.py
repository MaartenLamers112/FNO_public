"""Tests voor rolgebaseerde autorisatie."""

from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import PhotoRepository, RoleRepository, UserRepository


def create_photo() -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-AUTH-001",
            photo_number="AUTH-001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()
    return photo


def login_as(client, role_name: str) -> None:
    """Maak een gebruiker met de opgegeven rol en meld deze aan."""

    role_repository = RoleRepository()
    role = role_repository.create(name=role_name, description=role_name)
    role_repository.save()
    user_repository = UserRepository()
    user = user_repository.create(
        username=role_name,
        password_hash="tijdelijk",
        role_id=role.id,
    )
    user.set_password("test")
    user_repository.save()
    client.post(
        "/login",
        data={"username": role_name, "password": "test"},
    )


def test_visitor_cannot_create_label(client, app) -> None:
    """Een bezoeker zonder login kan geen label plaatsen."""

    photo = create_photo()
    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={"x_position": 0.2, "y_position": 0.3},
    )
    assert response.status_code == 401
    assert response.get_json()["code"] == "AUTHENTICATION_REQUIRED"


def test_employee_can_create_label(client, app) -> None:
    """Een medewerker kan een label plaatsen."""

    photo = create_photo()
    login_as(client, "employee")
    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={"x_position": 0.2, "y_position": 0.3},
    )
    assert response.status_code == 201


def test_administrator_can_create_label(client, app) -> None:
    """Een beheerder kan een label plaatsen."""

    photo = create_photo()
    login_as(client, "administrator")
    response = client.post(
        f"/api/photos/{photo.id}/persons",
        json={"x_position": 0.2, "y_position": 0.3},
    )
    assert response.status_code == 201
