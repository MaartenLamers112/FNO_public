"""Application factory voor Foto Nummeraar Online."""

from __future__ import annotations

from pathlib import Path

from flask import Flask

from app.api import register_api_blueprints
from app.api.errors import register_error_handlers
from app.auth import register_auth_blueprints
from app.core import register_web_blueprints
from app.extensions import csrf, db, login_manager, migrate
from app.logging import configure_logging
from config import get_config


def create_app(environment: str | None = None) -> Flask:
    """Maak en configureer een Flask-applicatie."""

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    app.config.from_object(get_config(environment))

    _ensure_runtime_directories(app)
    _validate_configuration(app)
    configure_logging(app)
    _load_models()
    _initialize_extensions(app)
    _configure_login_manager()
    register_api_blueprints(app)
    register_auth_blueprints(app)
    register_web_blueprints(app)
    register_error_handlers(app)

    return app


def _load_models() -> None:
    """Importeer alle modellen zodat SQLAlchemy ze registreert."""

    from app import models

    del models


def _ensure_runtime_directories(app: Flask) -> None:
    """Maak installatie-specifieke mappen aan indien nodig."""

    Path(app.instance_path).mkdir(
        parents=True,
        exist_ok=True,
    )

    log_directory = Path(app.config["LOG_DIR"])
    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


def _validate_configuration(app: Flask) -> None:
    """Controleer verplichte configuratie-instellingen."""

    secret_key = app.config.get("SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY ontbreekt. Maak een .env-bestand op basis van .env.example."
        )

    if app.config["DEBUG"] or app.config["TESTING"]:
        return

    _validate_production_configuration(app)


def _validate_production_configuration(app: Flask) -> None:
    """Weiger onveilige of onvolledige productieconfiguratie."""

    secret_key = str(app.config["SECRET_KEY"])
    if secret_key == "replace_with_random_secret_key" or len(secret_key) < 32:
        raise RuntimeError(
            "SECRET_KEY is niet geschikt voor productie. "
            "Gebruik een willekeurige sleutel van minimaal 32 tekens."
        )

    public_base_url = str(app.config.get("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if (
        not public_base_url.startswith("https://")
        or "localhost" in public_base_url.lower()
    ):
        raise RuntimeError(
            "PUBLIC_BASE_URL moet in productie een publieke HTTPS-URL zijn."
        )

    use_tls = bool(app.config["MAIL_USE_TLS"])
    use_ssl = bool(app.config["MAIL_USE_SSL"])
    if use_tls and use_ssl:
        raise RuntimeError("MAIL_USE_TLS en MAIL_USE_SSL mogen niet beide actief zijn.")

    if app.config["MAIL_SUPPRESS_SEND"]:
        return

    missing_mail_settings = [
        name for name in ("MAIL_SERVER", "MAIL_FROM") if not app.config.get(name)
    ]
    if missing_mail_settings:
        missing = ", ".join(missing_mail_settings)
        raise RuntimeError(f"SMTP-configuratie is onvolledig: {missing} ontbreekt.")

    username = app.config.get("MAIL_USERNAME")
    password = app.config.get("MAIL_PASSWORD")
    if bool(username) != bool(password):
        raise RuntimeError(
            "MAIL_USERNAME en MAIL_PASSWORD moeten beide ingesteld of beide leeg zijn."
        )


def _initialize_extensions(app: Flask) -> None:
    """Koppel alle Flask-extensies aan de applicatie."""

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"


def _configure_login_manager() -> None:
    """Configureer Flask-Login voor anonieme en ingelogde gebruikers."""

    from app.models import User
    from app.repositories import UserRepository

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Haal een gebruiker op voor Flask-Login."""

        if not user_id.isdigit():
            return None

        return UserRepository().get(int(user_id))
