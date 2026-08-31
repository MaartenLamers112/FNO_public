"""Basisklasse voor alle FNO-exceptions."""

from __future__ import annotations

from typing import Any


class FNOError(Exception):
    """Basisklasse voor alle domeinspecifieke fouten."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        return self.message
