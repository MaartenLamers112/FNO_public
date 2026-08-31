"""Exception voor fouten in externe services."""

from __future__ import annotations

from app.exceptions.fno_error import FNOError


class ExternalServiceError(FNOError):
    """Een externe service kon de aanvraag niet verwerken."""
