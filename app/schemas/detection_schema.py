"""API-schema's voor automatisch labelen."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.person_schema import PersonResponse


class AutoLabelResponse(BaseModel):
    """Resultaat van automatisch labelen."""

    model_config = ConfigDict(from_attributes=True)

    persons: list[PersonResponse]
    detected_count: int
    created_count: int
    skipped_existing_count: int
    model_name: str
    source_width: int
    source_height: int
    analysis_width: int
    analysis_height: int
    detection_passes: int
    image_load_duration_ms: int
    detector_load_duration_ms: int
    inference_duration_ms: int
    duration_ms: int
