"""Registratie van webblueprints."""

from __future__ import annotations

from flask import Flask

from app.core.routes import web_blueprint


def register_web_blueprints(app: Flask) -> None:
    """Registreer de routes voor de webinterface."""

    app.register_blueprint(web_blueprint)
