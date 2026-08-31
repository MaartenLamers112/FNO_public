"""Typen auteurs die een opmerking kunnen plaatsen."""

from enum import StrEnum


class AuthorType(StrEnum):
    """Ondersteunde auteurstypen."""

    VISITOR = "visitor"
    EMPLOYEE = "employee"
    ADMINISTRATOR = "administrator"
    SYSTEM = "system"
