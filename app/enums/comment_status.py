"""Statussen van opmerkingen binnen FNO."""

from enum import StrEnum


class CommentStatus(StrEnum):
    """Ondersteunde opmerkingstatussen."""

    OPEN = "open"
    RESOLVED = "resolved"
    CLOSED = "closed"
