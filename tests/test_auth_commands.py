"""Tests voor de authenticatiecommando's."""

from app.repositories import UserRepository


def test_create_admin_command_creates_administrator(app) -> None:
    """Het CLI-commando maakt een bruikbare beheerder aan."""

    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "create-admin",
            "--username",
            "beheerder",
            "--password",
            "zeer-veilig-wachtwoord",
        ]
    )

    assert result.exit_code == 0
    assert "Beheerder 'beheerder' is aangemaakt." in result.output

    user = UserRepository().get_by_username("beheerder")

    assert user is not None
    assert user.role.name == "administrator"
    assert user.check_password("zeer-veilig-wachtwoord") is True


def test_create_admin_command_rejects_duplicate_username(app) -> None:
    """Het CLI-commando weigert een bestaande gebruikersnaam."""

    runner = app.test_cli_runner()
    arguments = [
        "create-admin",
        "--username",
        "beheerder",
        "--password",
        "zeer-veilig-wachtwoord",
    ]

    first_result = runner.invoke(args=arguments)
    second_result = runner.invoke(args=arguments)

    assert first_result.exit_code == 0
    assert second_result.exit_code != 0
    assert "Gebruiker 'beheerder' bestaat al." in second_result.output
