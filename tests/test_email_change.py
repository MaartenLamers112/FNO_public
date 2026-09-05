"""Tests voor het wijzigen van het eigen e-mailadres."""

from app.extensions import db
from app.services import UserService


def login_registered_user(client):
    """Maak een geregistreerde gebruiker en meld deze aan."""

    user = UserService().create_user(
        username="emailtest",
        email="oud@example.nl",
        password="veiligwachtwoord",
        role_name="user",
    )
    user.email_verified = True
    db.session.commit()

    response = client.post(
        "/login",
        data={"username": "emailtest", "password": "veiligwachtwoord"},
    )
    assert response.status_code == 302
    return user


def test_change_email_page_requires_login(client) -> None:
    """Anonieme bezoekers worden naar aanmelden gestuurd."""

    response = client.get("/account/email")

    assert response.status_code == 302
    assert "/login?next=" in response.headers["Location"]


def test_user_can_change_own_email(app, client) -> None:
    """Een gebruiker kan het eigen adres wijzigen met huidig wachtwoord."""

    user = login_registered_user(client)

    response = client.post(
        "/account/email",
        data={"email": "Nieuw@Example.nl", "current_password": "veiligwachtwoord"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"nieuwe e-mailadres is opgeslagen" in response.data
    assert user.email == "nieuw@example.nl"
    assert user.email_verified is False


def test_email_change_requires_current_password(app, client) -> None:
    """Een verkeerd huidig wachtwoord blokkeert de wijziging."""

    user = login_registered_user(client)

    response = client.post(
        "/account/email",
        data={"email": "nieuw@example.nl", "current_password": "verkeerd"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"huidige wachtwoord is onjuist" in response.data
    assert user.email == "oud@example.nl"
    assert user.email_verified is True


def test_email_change_rejects_existing_email(app, client) -> None:
    """Een e-mailadres kan maar aan een account gekoppeld zijn."""

    UserService().create_user(
        username="bestaand",
        email="bestaand@example.nl",
        password="veiligwachtwoord",
        role_name="user",
    )
    user = login_registered_user(client)

    response = client.post(
        "/account/email",
        data={"email": "bestaand@example.nl", "current_password": "veiligwachtwoord"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"e-mailadres is al in gebruik" in response.data
    assert user.email == "oud@example.nl"
    assert user.email_verified is True


def test_account_menu_contains_password_reset_for_visitors(client) -> None:
    """Het sleuteltjemenu bevat de wachtwoord-vergetenlink."""

    response = client.get("/")

    assert response.status_code == 200
    assert b'href="/password/forgot"' in response.data
    assert b"Wachtwoord vergeten?" in response.data
