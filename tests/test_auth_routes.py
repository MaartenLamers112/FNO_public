"""Tests voor de authenticatieroutes."""

from app.repositories import RoleRepository, UserRepository


def create_user(
    *,
    username: str = "medewerker",
    password: str = "veilig-testwachtwoord",
    is_active: bool = True,
):
    """Maak een testgebruiker met medewerkersrol aan."""

    role_repository = RoleRepository()
    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    user_repository = UserRepository()
    user = user_repository.create(
        username=username,
        password_hash="tijdelijk",
        role_id=role.id,
        is_active=is_active,
    )
    user.set_password(password)
    user_repository.save()

    return user


def test_login_page_is_available(client) -> None:
    """De loginpagina is publiek bereikbaar."""

    response = client.get("/login")

    assert response.status_code == 200
    assert b"Aanmelden" in response.data
    assert b'name="username"' in response.data
    assert b'name="password"' in response.data


def test_valid_login_starts_session(app, client) -> None:
    """Geldige aanmeldgegevens starten een gebruikerssessie."""

    user = create_user()

    response = client.post(
        "/login",
        data={
            "username": "medewerker",
            "password": "veilig-testwachtwoord",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"medewerker" in response.data

    with client.session_transaction() as session:
        assert session["_user_id"] == str(user.id)

    assert user.last_login is not None


def test_invalid_login_shows_generic_message(app, client) -> None:
    """Ongeldige aanmeldgegevens tonen een generieke melding."""

    create_user()

    response = client.post(
        "/login",
        data={
            "username": "medewerker",
            "password": "verkeerd",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"De gebruikersnaam of het wachtwoord is onjuist." in response.data


def test_inactive_user_cannot_login(app, client) -> None:
    """Een inactieve gebruiker krijgt geen sessie."""

    create_user(is_active=False)

    response = client.post(
        "/login",
        data={
            "username": "medewerker",
            "password": "veilig-testwachtwoord",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Dit gebruikersaccount is niet actief." in response.data

    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_login_rejects_external_next_url(app, client) -> None:
    """Na aanmelden wordt niet naar een externe website doorgestuurd."""

    create_user()

    response = client.post(
        "/login",
        data={
            "username": "medewerker",
            "password": "veilig-testwachtwoord",
            "next": "https://example.com/onveilig",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_logout_ends_session(app, client) -> None:
    """Afmelden verwijdert de gebruikerssessie."""

    create_user()
    client.post(
        "/login",
        data={
            "username": "medewerker",
            "password": "veilig-testwachtwoord",
        },
    )

    response = client.post("/logout", follow_redirects=True)

    assert response.status_code == 200
    assert b"Je bent afgemeld." in response.data

    with client.session_transaction() as session:
        assert "_user_id" not in session


def test_logout_requires_authentication(client) -> None:
    """Een anonieme gebruiker wordt voor afmelden naar login gestuurd."""

    response = client.post("/logout")

    assert response.status_code == 302
    assert "/login?next=" in response.headers["Location"]
