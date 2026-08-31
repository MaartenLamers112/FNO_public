"""API-schema's voor vergelijking met Maior Memorix."""

from pydantic import BaseModel, Field

from app.enums.comparison_status import ComparisonStatus


class FieldComparisonResponse(BaseModel):
    """Vergelijking van één metadata-veld."""

    field: str
    mm_value: str
    fno_value: str
    equal: bool
    status: ComparisonStatus


class PersonComparisonResponse(BaseModel):
    """Vergelijking van één persoonsnaam op labelnummer."""

    label_number: int
    mm_name: str
    fno_name: str
    equal: bool
    status: ComparisonStatus


class PhotoComparisonResponse(BaseModel):
    """Volledige vergelijking van FNO- en MM-gegevens."""

    status: ComparisonStatus
    reliable: bool
    reason: str | None = None
    fields: list[FieldComparisonResponse]
    persons: list[PersonComparisonResponse] = Field(default_factory=list)
