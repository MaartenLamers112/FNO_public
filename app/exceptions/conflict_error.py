"""Exception voor conflicterende gegevens."""

from __future__ import annotations

from app.exceptions.fno_error import FNOError


class ConflictError(FNOError):
    """Conflicterende gegevens."""
