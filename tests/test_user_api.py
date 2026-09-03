"""Tests voor de gebruikersbeheer-API."""

from app.extensions import db
from app.models import User


def test_admin_can_create_user(client, authenticated_admin) -> None:
    """Een beheerder kan via de API een medewerker aanmaken."""

    response = client.post(
        "/api/users",
        json={"username": "nieuw", "password": "veilig123", "role": "employee"},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "id": 2,
        "username": "nieuw",
        "role": "employee",
        "is_active": True,
    }


def test_employee_cannot_list_users(client, authenticated_employee) -> None:
    """Een medewerker heeft geen toegang tot gebruikersbeheer."""

    response = client.get("/api/users")

    assert response.status_code == 403


def test_logged_in_user_can_change_own_password(
    app, client, authenticated_employee
) -> None:
    """Een ingelogde gebruiker kan via de API het eigen wachtwoord wijzigen."""

    response = client.post(
        "/api/users/me/password",
        json={"current_password": "test", "new_password": "nieuw123"},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 200
    user = db.session.get(User, 1)
    assert user.check_password("nieuw123") is True


def test_user_response_never_contains_password_hash(
    app, client, authenticated_admin
) -> None:
    """De gebruikers-API geeft nooit wachtwoordhashes terug."""

    response = client.get("/api/users")

    assert response.status_code == 200
    assert "password" not in response.get_data(as_text=True).lower()
