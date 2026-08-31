"""API-schema's voor foto-exports."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class ExportPersonResponse(BaseModel):
    """Persoonsgegevens binnen een foto-export."""

    id: int
    label_number: int
    name: str
    x_position: float
    y_position: float
    name_locked: bool


class ExportCommentResponse(BaseModel):
    """Opmerking binnen een foto-export."""

    id: int
    person_id: int | None
    content: str
    status: str


class PhotoExportResponse(BaseModel):
    """Technische export van één foto met personen en opmerkingen."""

    model_config = ConfigDict(from_attributes=True)

    photo: dict[str, Any]
    persons: list[ExportPersonResponse]
    comments: list[ExportCommentResponse]
