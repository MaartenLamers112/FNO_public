"""Registratie van authenticatieroutes en CLI-commando's."""

from __future__ import annotations

from flask import Flask

from app.auth.commands import register_auth_commands
from app.auth.routes import auth_blueprint


def register_auth_blueprints(app: Flask) -> None:
    """Registreer authenticatieroutes en -commando's."""

    app.register_blueprint(auth_blueprint)
    register_auth_commands(app)
