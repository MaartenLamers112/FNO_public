"""Centrale configuratie voor Foto Nummeraar Online."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
LOG_DIR = BASE_DIR / "logs"

load_dotenv(BASE_DIR / ".env")


def get_database_uri() -> str:
    """Geef de geconfigureerde database-URI terug."""

    configured_uri = os.getenv("DATABASE_URL")

    if configured_uri:
        return configured_uri

    database_path = (INSTANCE_DIR / "fno.db").as_posix()
    return f"sqlite:///{database_path}"


class BaseConfig:
    """Gemeenschappelijke configuratie voor alle omgevingen."""

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MM_API_BASE_URL = os.getenv(
        "MM_API_BASE_URL",
        "https://data.brabantcloud.nl/api",
    )
    MM_API_KEY = os.getenv("MM_API_KEY")
    MM_LANGUAGE = os.getenv("MM_LANGUAGE", "nl")
    MM_DATASET_SPEC = os.getenv("MM_DATASET_SPEC", "enb-119-beeldmateriaal")
    MM_TIMEOUT_SECONDS = float(os.getenv("MM_TIMEOUT_SECONDS", "10"))

    PERSON_DETECTION_MODEL_PATH = os.getenv(
        "PERSON_DETECTION_MODEL_PATH",
        str(BASE_DIR / "app" / "resources" / "face-detection-retail-0004.xml"),
    )
    PERSON_DETECTION_CONFIDENCE_THRESHOLD = float(
        os.getenv("PERSON_DETECTION_CONFIDENCE_THRESHOLD", "0.20")
    )
    PERSON_DETECTION_MAX_RESULTS = int(os.getenv("PERSON_DETECTION_MAX_RESULTS", "250"))
    PERSON_DETECTION_LABEL_MARGIN = float(
        os.getenv("PERSON_DETECTION_LABEL_MARGIN", "0.25")
    )
    PERSON_DETECTION_EXISTING_RADIUS = float(
        os.getenv("PERSON_DETECTION_EXISTING_RADIUS", "0.035")
    )

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_DIR = LOG_DIR
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "10"))

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(10 * 1024 * 1024)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False

    DEBUG = False
    TESTING = False


class DevelopmentConfig(BaseConfig):
    """Configuratie voor lokale ontwikkeling."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuratie voor geautomatiseerde tests."""

    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "fno-test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Configuratie voor productie."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True


CONFIGURATIONS: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(environment: str | None = None) -> type[BaseConfig]:
    """Selecteer de configuratie voor de opgegeven omgeving."""

    selected_environment = (
        environment or os.getenv("FLASK_ENV") or "development"
    ).lower()

    try:
        return CONFIGURATIONS[selected_environment]
    except KeyError as exc:
        supported = ", ".join(sorted(CONFIGURATIONS))

        raise ValueError(
            f"Onbekende omgeving '{selected_environment}'. "
            f"Ondersteunde omgevingen: {supported}."
        ) from exc
