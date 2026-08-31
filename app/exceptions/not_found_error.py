"""Exception voor ontbrekende objecten."""

from __future__ import annotations

from app.exceptions.fno_error import FNOError


class NotFoundError(FNOError):
    """Object bestaat niet."""
