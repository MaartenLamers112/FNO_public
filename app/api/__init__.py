"""Registratie van REST API-blueprints."""

from __future__ import annotations

from flask import Flask

from app.api.health import health_blueprint
from app.api.persons import persons_blueprint
from app.api.photos import photos_blueprint
from app.api.users import users_blueprint


def register_api_blueprints(app: Flask) -> None:
    """Registreer alle REST API-blueprints."""

    app.register_blueprint(
        health_blueprint,
        url_prefix="/api",
    )

    app.register_blueprint(photos_blueprint)
    app.register_blueprint(persons_blueprint)
    app.register_blueprint(users_blueprint)
