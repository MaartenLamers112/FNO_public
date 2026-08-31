"""Tests voor het beheerdashboard."""

from app.extensions import db
from app.models import Role, User


def create_user(*, role_name: str, username: str) -> User:
    """Maak een testgebruiker met rol aan."""

    role = Role(name=role_name, description=role_name)
    user = User(username=username, role=role)
    user.set_password("test")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, username: str) -> None:
    """Meld een testgebruiker aan."""

    client.post(
        "/login",
        data={"username": username, "password": "test"},
        follow_redirects=False,
    )


def test_dashboard_requires_authentication(client) -> None:
    """Een bezoeker krijgt geen toegang tot het dashboard."""

    response = client.get("/admin")

    assert response.status_code == 401


def test_employee_can_view_dashboard(app, client) -> None:
    """Een medewerker kan het dashboard bekijken."""

    with app.app_context():
        create_user(role_name="employee", username="medewerker")

    login(client, "medewerker")
    response = client.get("/admin")

    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"concept" in response.data
    assert b"Belangrijke activiteiten" in response.data


def test_visitor_does_not_see_label_controls(client) -> None:
    """Een bezoeker ziet geen labelbeheerknoppen in de HTML."""

    response = client.get("/photos/1")

    assert response.status_code == 200
    assert b'id="toggle-label-placement"' not in response.data
    assert b'id="delete-person-label"' not in response.data
    assert b"Nieuw label plaatsen" not in response.data
