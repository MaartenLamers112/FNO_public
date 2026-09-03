"""Tests voor de UI van onbevestigde gebruikersaccounts."""

from app.services import UserService


def test_unverified_user_gets_read_only_photo_ui(app, client) -> None:
    """Een onbevestigde gebruiker ziet geen bewerkbare foto-invoer."""

    UserService().register_user(
        username="gebruiker",
        email="gebruiker@example.nl",
        password="veilig123",
    )
    client.post(
        "/login",
        data={
            "username": "gebruiker",
            "password": "veilig123",
        },
    )

    response = client.get("/photos/bestaat-niet")

    assert response.status_code == 404
    assert b'data-can-contribute="false"' in response.data
    assert b'id="photo-subject"' in response.data
    assert b"disabled" in response.data
