"""Regressietests voor productieconfiguratie."""

import pytest
from flask import Flask

from app import _validate_configuration


def _production_app() -> Flask:
    """Maak een minimale geldige productieconfiguratie."""

    app = Flask(__name__)
    app.config.update(
        DEBUG=False,
        TESTING=False,
        SECRET_KEY="x" * 32,
        PUBLIC_BASE_URL="https://fno.example.nl",
        MAIL_SERVER="smtp.example.nl",
        MAIL_FROM="fno@example.nl",
        MAIL_USERNAME="account",
        MAIL_PASSWORD="secret",
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_SUPPRESS_SEND=False,
    )
    return app


def test_production_rejects_example_secret_key() -> None:
    """Een voorbeeldsleutel mag productie niet starten."""

    app = _production_app()
    app.config["SECRET_KEY"] = "replace_with_random_secret_key"

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _validate_configuration(app)


def test_production_rejects_short_secret_key() -> None:
    """Een te korte productiesleutel wordt geweigerd."""

    app = _production_app()
    app.config["SECRET_KEY"] = "te-kort"

    with pytest.raises(RuntimeError, match="minimaal 32"):
        _validate_configuration(app)


def test_production_requires_public_https_base_url() -> None:
    """Accountlinks moeten naar een publieke HTTPS-basis-URL verwijzen."""

    app = _production_app()
    app.config["PUBLIC_BASE_URL"] = "http://localhost:5000"

    with pytest.raises(RuntimeError, match="PUBLIC_BASE_URL"):
        _validate_configuration(app)


def test_production_rejects_tls_and_ssl_together() -> None:
    """SMTP mag niet tegelijk TLS en SSL afdwingen."""

    app = _production_app()
    app.config["MAIL_USE_SSL"] = True

    with pytest.raises(RuntimeError, match="MAIL_USE_TLS"):
        _validate_configuration(app)


def test_production_requires_smtp_when_mail_is_enabled() -> None:
    """Ingeschakelde mail vereist minimaal server en afzender."""

    app = _production_app()
    app.config["MAIL_SERVER"] = None

    with pytest.raises(RuntimeError, match="MAIL_SERVER"):
        _validate_configuration(app)


def test_production_allows_suppressed_mail_without_smtp() -> None:
    """Een expliciet mail-loze installatie mag zonder SMTP starten."""

    app = _production_app()
    app.config.update(
        MAIL_SUPPRESS_SEND=True,
        MAIL_SERVER=None,
        MAIL_FROM=None,
        MAIL_USERNAME=None,
        MAIL_PASSWORD=None,
    )

    _validate_configuration(app)


def test_production_requires_complete_smtp_credentials() -> None:
    """SMTP-inloggegevens moeten als compleet paar worden ingesteld."""

    app = _production_app()
    app.config["MAIL_PASSWORD"] = None

    with pytest.raises(RuntimeError, match="MAIL_USERNAME"):
        _validate_configuration(app)
