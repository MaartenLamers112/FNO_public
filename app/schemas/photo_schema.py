"""API-schema's voor foto's."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.enums.publication_status import PublicationStatus
from app.schemas.comparison_schema import PhotoComparisonResponse


class PhotoResponse(BaseModel):
    """Representatie van een foto in de REST API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    mm_id: str
    photo_number: str
    publication_status: PublicationStatus
    progress_status: str = "empty"
    is_visible: bool = False
    is_complete: bool = False

    @field_serializer("publication_status")
    def serialize_publication_status(
        self,
        value: PublicationStatus,
    ) -> str:
        """Zet de enum om naar een leesbare API-waarde."""

        return value.name.lower()


class PhotoPublicDetailResponse(PhotoResponse):
    """Publieke foto-informatie met live MM-brongegevens."""

    image_source: str
    person_display_mode: Literal["numbered", "left_to_right", "single_person"] = (
        "numbered"
    )
    label_size: int = 14
    person_display_count: int = 1
    subject: str
    date: str
    location: str
    description: str
    previous_photo_id: int | None
    next_photo_id: int | None


class PhotoDetailResponse(PhotoPublicDetailResponse):
    """Beheerfoto met vergelijking tussen FNO en MM."""

    comparison: PhotoComparisonResponse


class PhotoPublicLandingItemResponse(PhotoResponse):
    """Publieke foto-informatie voor raster- en lijstweergave."""

    thumbnail_url: str
    subject: str
    date: str
    location: str


class PhotoLandingItemResponse(PhotoPublicLandingItemResponse):
    """Foto-informatie voor raster- en lijstweergave."""

    thumbnail_url: str
    subject: str
    date: str
    comparison: PhotoComparisonResponse


class PhotoPublicCollectionResponse(BaseModel):
    """Publiek landingspaginaresultaat zonder MM-vergelijking."""

    items: list[PhotoPublicLandingItemResponse]
    locations: list[str]


class PhotoCollectionResponse(BaseModel):
    """Landingspaginaresultaat met beschikbare plaatsfilters."""

    items: list[PhotoLandingItemResponse]
    locations: list[str]


class PhotoMetadataUpdate(BaseModel):
    """Lokale bewerkbare metadata van een foto."""

    subject: str = ""
    date: str = ""
    location: str = ""
    description: str = ""


class PhotoPersonDisplayModeUpdate(BaseModel):
    """Weergave van personen op een foto."""

    person_display_mode: Literal["numbered", "left_to_right", "single_person"]
    person_display_count: int = 1


class PhotoPersonDisplayModeResponse(BaseModel):
    """Actuele personenweergave van een foto."""

    id: int
    person_display_mode: Literal["numbered", "left_to_right", "single_person"]
    person_display_count: int


class PhotoLabelSizeUpdate(BaseModel):
    """Lettergrootte van labels op een foto."""

    label_size: int


class PhotoLabelSizeResponse(BaseModel):
    """Actuele labelgrootte van een foto."""

    id: int
    label_size: int


class PhotoManagementUpdate(BaseModel):
    """Beheervelden voor zichtbaarheid en gereedmelding."""

    is_visible: bool
    is_complete: bool


class PhotoPublicationStatusUpdate(BaseModel):
    """Nieuwe publicatiestatus voor een foto."""

    publication_status: PublicationStatus
    progress_status: str = "empty"
    is_visible: bool = False
    is_complete: bool = False

    @field_validator("publication_status", mode="before")
    @classmethod
    def parse_publication_status(cls, value: object) -> PublicationStatus:
        """Vertaal een leesbare statusnaam naar de interne enum."""

        if isinstance(value, PublicationStatus):
            return value

        normalized = str(value).strip().upper()

        try:
            return PublicationStatus[normalized]
        except KeyError as exc:
            raise ValueError("Ongeldige publicatiestatus.") from exc


class PhotoListQuery(BaseModel):
    """Gevalideerde queryparameters voor het foto-overzicht."""

    search: str = ""
    status: Literal["empty", "partial", "complete"] | None = None
    location: str = ""
    sort: Literal[
        "photo_number",
        "subject",
        "date",
        "location",
        "status",
    ] = "photo_number"
    direction: Literal["asc", "desc"] = "asc"

    @field_validator("search", "location", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        """Normaliseer optionele tekstfilters."""

        return "" if value is None else str(value).strip()
