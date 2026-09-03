"""Typen auteurs die een opmerking kunnen plaatsen."""

from enum import StrEnum


class AuthorType(StrEnum):
    """Ondersteunde auteurstypen."""

    VISITOR = "visitor"
    USER = "user"
    EMPLOYEE = "employee"
    ADMINISTRATOR = "administrator"
    SYSTEM = "system"
