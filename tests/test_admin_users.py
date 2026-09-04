"""Tests voor compact gebruikersbeheer."""

from datetime import datetime

from app.extensions import db
from app.models import Role, User
from app.services import UserService


def login_user(client, *, username: str, role_name: str) -> User:
    """Maak en login een testgebruiker."""

    role = Role(name=role_name, description=role_name)
    user = User(
        username=username,
        email=f"{username}@example.nl",
        email_verified=True,
        role=role,
    )
    user.set_password("veilig123")
    db.session.add(user)
    db.session.commit()
    client.post(
        "/login",
        data={"username": username, "password": "veilig123"},
    )
    return user


def test_regular_user_does_not_see_admin_navigation(app, client) -> None:
    """Een gewone gebruiker ziet geen Beheer-tab."""

    login_user(client, username="gebruiker", role_name="user")

    response = client.get("/")

    assert response.status_code == 200
    assert b'href="/admin"' not in response.data


def test_admin_users_page_shows_compact_table_and_email(app, client) -> None:
    """Gebruikersbeheer toont e-mail en tabelhulpmiddelen."""

    login_user(client, username="beheerder", role_name="administrator")
    user = UserService().create_user(
        username="voorbeeld",
        email="voorbeeld@example.nl",
        password="veilig123",
        role_name="user",
    )
    user.last_login = datetime(2026, 9, 4, 18, 30)
    db.session.commit()

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b'id="user-search"' in response.data
    assert b'id="user-table"' in response.data
    assert b"voorbeeld@example.nl" in response.data
    assert b"Laatste login" in response.data
    assert b'data-last-login="2026-09-04T18:30:00Z"' in response.data
    assert b"admin-users.js" in response.data


def test_admin_can_delete_unused_user(app, client) -> None:
    """Een beheerder kan een ongebruikt testaccount verwijderen."""

    login_user(client, username="beheerder", role_name="administrator")
    user = UserService().create_user(
        username="verwijderbaar",
        email="verwijderbaar@example.nl",
        password="veilig123",
        role_name="user",
    )

    response = client.post(
        "/admin/users",
        data={"action": "delete", "user_id": str(user.id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert UserService().repository.get(user.id) is None
    assert b"Gebruiker verwijderd." in response.data


def test_admin_cannot_delete_own_account(app, client) -> None:
    """Een beheerder kan het eigen account niet verwijderen."""

    admin = login_user(
        client,
        username="beheerder",
        role_name="administrator",
    )

    response = client.post(
        "/admin/users",
        data={"action": "delete", "user_id": str(admin.id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert UserService().repository.get(admin.id) is not None
    assert b"eigen beheerdersaccount niet verwijderen" in response.data
