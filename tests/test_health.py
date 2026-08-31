"""Tests voor de algemene healthcheck."""

from flask.testing import FlaskClient


def test_healthcheck(client: FlaskClient) -> None:
    """De healthcheck geeft een succesvolle JSON-response."""

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "application": "Foto Nummeraar Online",
        "status": "ok",
    }


def test_security_cookie_defaults(app) -> None:
    """De standaard sessiecookie gebruikt veilige browserinstellingen."""

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_upload_size_limit_is_configured(app) -> None:
    """Uploads hebben een vaste maximale requestgrootte."""

    assert app.config["MAX_CONTENT_LENGTH"] == 10 * 1024 * 1024
