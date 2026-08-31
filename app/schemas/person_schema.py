"""API-schema's voor personen en fotolabels."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PersonCreate(BaseModel):
    """Positie voor een nieuw persoonslabel."""

    x_position: float
    y_position: float


class PersonPositionUpdate(BaseModel):
    """Nieuwe relatieve positie van een persoonslabel."""

    x_position: float
    y_position: float


class PersonNumberUpdate(BaseModel):
    """Nieuw nummer voor een persoonslabel."""

    label_number: int


class PersonNameUpdate(BaseModel):
    """Nieuwe naam voor een persoon."""

    current_name: str | None


class PersonLockUpdate(BaseModel):
    """Nieuwe vergrendelstatus van een naam."""

    name_locked: bool


class PersonResponse(BaseModel):
    """Representatie van een persoonslabel in de REST API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    photo_id: int
    label_number: int
    x_position: float
    y_position: float
    current_name: str | None
    name_locked: bool
