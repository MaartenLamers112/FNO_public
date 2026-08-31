"""Gedeelde pytest-fixtures voor FNO."""

from collections.abc import Generator

import pytest
from flask import Flask

from app import create_app
from app.extensions import db
from app.models import Role, User


@pytest.fixture()
def app() -> Generator[Flask]:
    """Maak een geïsoleerde Flask-testapplicatie."""

    test_app = create_app("testing")

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app: Flask):
    """Geef een Flask-testclient terug."""

    return app.test_client()


def _create_authenticated_user(client, *, role_name: str, username: str) -> None:
    """Maak een gebruiker en meld deze aan via de testclient."""

    role = Role(name=role_name, description=role_name)
    user = User(username=username, role=role)
    user.set_password("test")
    db.session.add(user)
    db.session.commit()
    client.post("/login", data={"username": username, "password": "test"})


@pytest.fixture()
def authenticated_employee(app: Flask, client) -> None:
    """Meld een medewerker aan voor routetests."""

    with app.app_context():
        _create_authenticated_user(
            client,
            role_name="employee",
            username="medewerker",
        )


@pytest.fixture()
def authenticated_admin(app: Flask, client) -> None:
    """Meld een beheerder aan voor routetests."""

    with app.app_context():
        _create_authenticated_user(
            client,
            role_name="administrator",
            username="beheerder",
        )
