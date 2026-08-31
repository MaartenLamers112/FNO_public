"""Exception voor onvoldoende rechten."""

from __future__ import annotations

from app.exceptions.fno_error import FNOError


class AuthorizationError(FNOError):
    """Gebruiker heeft onvoldoende rechten."""
