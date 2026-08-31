"""Statussen voor vergelijking tussen FNO en Maior Memorix."""

from enum import StrEnum


class ComparisonStatus(StrEnum):
    """Resultaatstatus van een MM-vergelijking."""

    GREEN = "green"
    ORANGE = "orange"
    RED = "red"
