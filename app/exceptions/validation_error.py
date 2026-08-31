"""Exception voor ongeldige invoer."""

from __future__ import annotations

from app.exceptions.fno_error import FNOError


class ValidationError(FNOError):
    """Validatie is mislukt."""
