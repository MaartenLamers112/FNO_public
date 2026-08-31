"""CLI-commando's voor FNO-authenticatie."""

from __future__ import annotations

import click
from flask import Flask

from app.exceptions import ConflictError, ValidationError
from app.services import UserService


def register_auth_commands(app: Flask) -> None:
    """Registreer authenticatiecommando's bij Flask."""

    app.cli.add_command(create_admin)


@click.command("create-admin")
@click.option(
    "--username",
    prompt="Gebruikersnaam",
    help="Gebruikersnaam van de nieuwe beheerder.",
)
@click.password_option(
    confirmation_prompt=True,
    help="Wachtwoord van de nieuwe beheerder.",
)
def create_admin(username: str, password: str) -> None:
    """Maak de eerste beheerder aan."""

    try:
        user = UserService().create_administrator(
            username=username,
            password=password,
        )
    except (ConflictError, ValidationError) as error:
        raise click.ClickException(str(error)) from error

    click.echo(f"Beheerder '{user.username}' is aangemaakt.")
