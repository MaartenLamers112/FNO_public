"""API-schema's voor gebruikersbeheer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Veilige representatie van een FNO-gebruiker."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Literal["employee", "administrator"]
    is_active: bool


class UserCreate(BaseModel):
    """Gegevens voor een nieuw gebruikersaccount."""

    username: str
    password: str
    role: Literal["employee", "administrator"]


class UserUpdate(BaseModel):
    """Bewerkbare beheervelden van een gebruikersaccount."""

    username: str
    role: Literal["employee", "administrator"]
    is_active: bool


class UserPasswordReset(BaseModel):
    """Nieuw wachtwoord dat een beheerder instelt."""

    password: str


class OwnPasswordUpdate(BaseModel):
    """Wachtwoordwijziging door de ingelogde gebruiker."""

    current_password: str
    new_password: str
