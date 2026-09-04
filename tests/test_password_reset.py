"""Tests voor wachtwoordherstel via e-mail."""

from app.services import PasswordResetService, UserService


def create_user():
    """Maak een actieve geregistreerde testgebruiker."""

    return UserService().create_user(
        username="hersteltest",
        email="hersteltest@example.nl",
        password="oudwachtwoord",
        role_name="user",
    )


def test_login_page_links_to_forgot_password(client) -> None:
    """De aanmeldpagina biedt wachtwoordherstel aan."""

    response = client.get("/login")

    assert response.status_code == 200
    assert b"/password/forgot" in response.data
    assert b"Wachtwoord vergeten" in response.data


def test_forgot_password_response_does_not_reveal_account(client) -> None:
    """Een aanvraag voor een onbekend adres geeft generieke feedback."""

    response = client.post(
        "/password/forgot",
        data={"email": "onbekend@example.nl"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Als het e-mailadres bij een actief account hoort" in response.data


def test_password_can_be_reset_with_valid_token(app, client) -> None:
    """Een geldig token kan het wachtwoord wijzigen."""

    user = create_user()
    token = PasswordResetService().create_token(user)

    response = client.post(
        f"/password/reset/{token}",
        data={
            "password": "nieuwwachtwoord",
            "password_confirmation": "nieuwwachtwoord",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Je wachtwoord is gewijzigd." in response.data

    authenticated = UserService().authenticate(
        username="hersteltest",
        password="nieuwwachtwoord",
    )
    assert authenticated.id == user.id


def test_password_reset_token_is_invalid_after_use(app, client) -> None:
    """Een gebruikt token kan niet opnieuw worden gebruikt."""

    user = create_user()
    token = PasswordResetService().create_token(user)

    first = client.post(
        f"/password/reset/{token}",
        data={
            "password": "nieuwwachtwoord",
            "password_confirmation": "nieuwwachtwoord",
        },
    )
    second = client.post(
        f"/password/reset/{token}",
        data={
            "password": "nogmaalsnieuw",
            "password_confirmation": "nogmaalsnieuw",
        },
        follow_redirects=True,
    )

    assert first.status_code == 302
    assert second.status_code == 200
    assert b"niet meer geldig" in second.data
