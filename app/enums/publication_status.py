"""
Publicatiestatus van een foto.
"""

from enum import IntEnum


class PublicationStatus(IntEnum):
    """Publicatiestatus volgens het STD."""

    CONCEPT = 0
    PUBLISHED = 1
    HIDDEN = 2
