"""Tests voor FNO exceptions."""

from app.exceptions import (
    ConflictError,
    FNOError,
    NotFoundError,
)


def test_fno_error_properties() -> None:
    """Alle eigenschappen worden correct opgeslagen."""

    error = FNOError(
        "Test fout",
        code="TEST_ERROR",
        details={
            "id": 123,
        },
    )

    assert error.message == "Test fout"
    assert error.code == "TEST_ERROR"
    assert error.details == {"id": 123}


def test_fno_error_string() -> None:
    """De stringrepresentatie bevat het bericht."""

    error = FNOError("Hallo")

    assert str(error) == "Hallo"


def test_exceptions_inherit_from_fno_error() -> None:
    """Alle domeinexceptions erven van FNOError."""

    assert isinstance(
        ConflictError("Conflict"),
        FNOError,
    )

    assert isinstance(
        NotFoundError("Niet gevonden"),
        FNOError,
    )
