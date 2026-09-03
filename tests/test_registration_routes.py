"""Tests voor openbare registratie- en verificatieroutes."""

from app.repositories import UserRepository
from app.services import EmailVerificationService


def test_registration_page_is_public(client) -> None:
    """De registratiepagina is publiek bereikbaar."""

    response = client.get("/register")

    assert response.status_code == 200
    assert b"Registreren" in response.data
    assert b'name="email"' in response.data


def test_registration_creates_account(app, client) -> None:
    """Een geldig registratieformulier maakt een account aan."""

    response = client.post(
        "/register",
        data={
            "username": "gebruiker",
            "email": "gebruiker@example.nl",
            "password": "veilig123",
            "password_confirmation": "veilig123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Je account is aangemaakt." in response.data

    user = UserRepository().get_by_username("gebruiker")
    assert user is not None
    assert user.role.name == "user"
    assert user.email_verified is False


def test_verification_route_confirms_account(app, client) -> None:
    """Een geldige verificatielink bevestigt het account."""

    client.post(
        "/register",
        data={
            "username": "gebruiker",
            "email": "gebruiker@example.nl",
            "password": "veilig123",
            "password_confirmation": "veilig123",
        },
    )
    user = UserRepository().get_by_username("gebruiker")
    token = EmailVerificationService().create_token(user)

    response = client.get(
        f"/verify-email/{token}",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Je e-mailadres is bevestigd." in response.data
    assert UserRepository().get(user.id).email_verified is True


def test_resend_route_does_not_reveal_unknown_email(client) -> None:
    """Opnieuw versturen lekt niet of een account bestaat."""

    response = client.post(
        "/verify-email/resend",
        data={"email": "onbekend@example.nl"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Als het e-mailadres bij een onbevestigd account hoort" in response.data
