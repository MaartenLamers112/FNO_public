"""Bedrijfslogica voor bulkimport uit Maior Memorix."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.exceptions import NotFoundError
from app.models import MmImportJob, Photo
from app.repositories import HistoryRepository, MmImportJobRepository, PhotoRepository
from app.services.base_service import BaseService
from app.services.memorix_service import MemorixService

FACET_FILTER_FIELDS = {
    "collection_part": "tib_collectionPart",
    "collection": "tib_collection",
    "place": "tib_place",
    "municipality": "tib_municipality",
    "subject": "dc_subject",
}

FILTER_FIELDS = {
    "collection_part": "tib_collectionPart_facet",
    "collection": "tib_collection_facet",
    "place": "tib_place_facet",
    "municipality": "tib_municipality_facet",
    "subject": "dc_subject_facet",
    "title": "dc_title",
    "description": "dc_description",
    "photo_number": "dc_identifier",
    "date": "dcterms_created",
}


@dataclass(frozen=True)
class ImportPreview:
    """Voorvertoning van één MM-zoekopdracht."""

    records: list[dict[str, Any]]
    found_count: int
    new_count: int
    existing_count: int
    invalid_count: int
    page: int
    page_size: int
    page_count: int


@dataclass(frozen=True)
class MetadataSupplementResult:
    """Samenvatting van expliciet aanvullen vanuit MM."""

    checked_photos: int
    matched_photos: int
    updated_photos: int
    updated_fields: int
    missing_photos: int


class MmImportService(BaseService[MmImportJobRepository]):
    """Zoek en importeer MM-records als lokale conceptfoto's."""

    def __init__(
        self,
        *,
        photo_repository: PhotoRepository | None = None,
        job_repository: MmImportJobRepository | None = None,
        history_repository: HistoryRepository | None = None,
        memorix_service: MemorixService | None = None,
    ) -> None:
        resolved_job_repository = job_repository or MmImportJobRepository()
        super().__init__(resolved_job_repository)
        self.photo_repository = photo_repository or PhotoRepository()
        self.job_repository = resolved_job_repository
        self.history_repository = history_repository or HistoryRepository()
        self.memorix_service = memorix_service or MemorixService()

    def get_filter_options(self) -> dict[str, list[str]]:
        """Geef live keuzelijsten voor de belangrijkste MM-filters."""

        return {
            key: self.memorix_service.get_facet_values(field)
            for key, field in FACET_FILTER_FIELDS.items()
        }

    def preview(
        self,
        filters: dict[str, str],
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> ImportPreview:
        """Geef één snelle pagina voorvertoningsrecords."""

        mm_filters = self._normalize_filters(filters)
        raw_records, found_count = self.memorix_service.search_records_page(
            filters=mm_filters,
            page=page,
            page_size=page_size,
        )
        records = [
            self.memorix_service.normalize_search_record(record)
            for record in raw_records
        ]
        mm_ids = {record["mm_id"] for record in records if record["mm_id"]}
        existing_by_mm_id = {
            photo.mm_id: photo for photo in self.photo_repository.get_by_mm_ids(mm_ids)
        }
        for record in records:
            existing_photo = existing_by_mm_id.get(record["mm_id"])
            record["exists"] = existing_photo is not None
            record["photo_id"] = (
                existing_photo.id if existing_photo is not None else None
            )
            record["valid"] = bool(record["mm_id"] and record["photo_number"])

        page_count = max((found_count + page_size - 1) // page_size, 1)
        current_page = min(max(page, 1), page_count)
        return ImportPreview(
            records=records,
            found_count=found_count,
            new_count=sum(
                record["valid"] and not record["exists"] for record in records
            ),
            existing_count=sum(record["exists"] for record in records),
            invalid_count=sum(not record["valid"] for record in records),
            page=current_page,
            page_size=page_size,
            page_count=page_count,
        )

    def import_selected(
        self,
        *,
        filters: dict[str, str],
        selected_mm_ids: set[str],
        user_id: int,
        page: int = 1,
    ) -> MmImportJob:
        """Importeer de geselecteerde geldige nieuwe MM-records."""

        preview = self.preview(filters, page=page)
        imported = 0
        failed = 0

        for record in preview.records:
            if record["mm_id"] not in selected_mm_ids:
                continue
            if record["exists"] or not record["valid"]:
                continue
            if self.photo_repository.get_by_photo_number(record["photo_number"]):
                failed += 1
                continue

            photo = self.photo_repository.add(
                Photo(
                    mm_id=record["mm_id"],
                    photo_number=record["photo_number"],
                    publication_status=PublicationStatus.CONCEPT,
                    mm_metadata=record["fields"],
                    **self._build_local_metadata(record["fields"]),
                    is_visible=False,
                    is_complete=False,
                )
            )
            self.photo_repository.flush()
            self.history_repository.create(
                photo_id=photo.id,
                user_id=user_id,
                event_type=HistoryEventType.PHOTO_IMPORTED,
                description="Foto uit Maior Memorix toegevoegd",
                new_value=record["mm_id"],
            )
            imported += 1

        job = self.job_repository.add(
            MmImportJob(
                user_id=user_id,
                filters=filters,
                found_count=preview.found_count,
                imported_count=imported,
                skipped_count=preview.existing_count,
                failed_count=preview.invalid_count + failed,
            )
        )
        self._commit()
        return job

    def supplement_missing_metadata(
        self,
        *,
        user_id: int | None,
    ) -> MetadataSupplementResult:
        """Vul uitsluitend lege lokale metadata vanuit actuele MM-gegevens."""

        photos = self.photo_repository.get_all()
        photos_to_supplement = [
            photo
            for photo in photos
            if any(
                self._is_empty(value)
                for value in (
                    photo.local_subject,
                    photo.local_date,
                    photo.local_location,
                    photo.local_description,
                )
            )
        ]
        if not photos_to_supplement:
            return MetadataSupplementResult(
                checked_photos=len(photos),
                matched_photos=0,
                updated_photos=0,
                updated_fields=0,
                missing_photos=0,
            )

        total_started = perf_counter()
        matched_ids: set[str] = set()
        updated_photo_ids: set[int] = set()
        updated_fields = 0
        mm_duration = 0.0
        processing_duration = 0.0

        for photo in photos_to_supplement:
            mm_started = perf_counter()
            try:
                fields, metadata = self.memorix_service.get_metadata_record(photo.mm_id)
            except NotFoundError:
                mm_duration += perf_counter() - mm_started
                continue
            mm_duration += perf_counter() - mm_started

            processing_started = perf_counter()
            matched_ids.add(photo.mm_id)
            photo.mm_metadata = fields

            for attribute, value, label in (
                ("local_subject", metadata.subject, "Onderwerp"),
                ("local_date", metadata.date, "Datering"),
                ("local_location", metadata.location, "Locatie"),
                (
                    "local_description",
                    metadata.description,
                    "Beschrijving",
                ),
            ):
                current_value = getattr(photo, attribute)
                if not self._is_empty(current_value) or not value:
                    continue

                setattr(photo, attribute, value)
                self.history_repository.create(
                    photo_id=photo.id,
                    user_id=user_id,
                    event_type=HistoryEventType.METADATA_CHANGED,
                    description=f"{label} aangevuld vanuit Maior Memorix",
                    old_value=current_value,
                    new_value=value,
                )
                updated_photo_ids.add(photo.id)
                updated_fields += 1
            processing_duration += perf_counter() - processing_started

        save_started = perf_counter()
        self._commit()
        save_duration = perf_counter() - save_started
        total_duration = perf_counter() - total_started

        print(
            "[FNO timing] MM ophalen: "
            f"{mm_duration:.2f}s | Verwerken: {processing_duration:.2f}s | "
            f"Opslaan: {save_duration:.2f}s | Totaal: {total_duration:.2f}s | "
            f"MM-records: {len(matched_ids)} | "
            f"FNO te controleren: {len(photos_to_supplement)}"
        )

        return MetadataSupplementResult(
            checked_photos=len(photos),
            matched_photos=len(matched_ids),
            updated_photos=len(updated_photo_ids),
            updated_fields=updated_fields,
            missing_photos=len(photos_to_supplement) - len(matched_ids),
        )

    @staticmethod
    def _is_empty(value: str | None) -> bool:
        """Behandel None en alleen-witruimte als lege lokale metadata."""

        return value is None or not value.strip()

    def _build_local_metadata(self, fields: dict[str, Any]) -> dict[str, str | None]:
        """Vertaal MM-velden naar de lokale fotometadatakolommen."""

        metadata = self.memorix_service.get_local_metadata_from_fields(fields)
        return {
            "local_subject": metadata["subject"] or None,
            "local_date": metadata["date"] or None,
            "local_location": metadata["location"] or None,
            "local_description": metadata["description"] or None,
        }

    @staticmethod
    def _normalize_filters(filters: dict[str, str]) -> dict[str, str]:
        """Vertaal gebruikersfilters naar MM-veldnamen."""

        return {
            FILTER_FIELDS[key]: value.strip()
            for key, value in filters.items()
            if key in FILTER_FIELDS and value.strip()
        }
