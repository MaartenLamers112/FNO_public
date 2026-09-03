"""API-schema's voor gebruikersbeheer."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

UserRole = Literal["user", "employee", "administrator"]


class UserResponse(BaseModel):
    """Veilige representatie van een FNO-gebruiker."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    email_verified: bool
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    """Gegevens voor een nieuw gebruikersaccount."""

    username: str
    email: str | None = None
    password: str
    role: UserRole


class UserUpdate(BaseModel):
    """Bewerkbare beheervelden van een gebruikersaccount."""

    username: str
    role: UserRole
    is_active: bool


class UserPasswordReset(BaseModel):
    """Nieuw wachtwoord dat een beheerder instelt."""

    password: str


class OwnPasswordUpdate(BaseModel):
    """Wachtwoordwijziging door de ingelogde gebruiker."""

    current_password: str
    new_password: str
