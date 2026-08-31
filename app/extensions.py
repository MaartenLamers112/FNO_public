"""Centrale declaratie van Flask-extensies."""

from __future__ import annotations

import sqlite3

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Basisklasse voor SQLAlchemy."""


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection: object,
    connection_record: object,
) -> None:
    """Schakel foreign-keyhandhaving in voor SQLite-verbindingen."""

    del connection_record

    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()
