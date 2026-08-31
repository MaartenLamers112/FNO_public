"""Communicatie met de BrabantCloud/Maior Memorix API."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from flask import current_app

from app.exceptions import ExternalServiceError, NotFoundError


@dataclass(frozen=True)
class MemorixMetadata:
    """Genormaliseerde MM-metadata voor FNO-gebruik."""

    subject: str
    date: str
    location: str
    description: str
    description_raw: str

    def as_local_values(self) -> dict[str, str]:
        """Geef de vier lokaal beheerde metadatawaarden terug."""

        return {
            "subject": self.subject,
            "date": self.date,
            "location": self.location,
            "description": self.description,
        }


class MemorixService:
    """Haal live brongegevens op uit Maior Memorix."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        language: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        """Initialiseer de service met configureerbare verbindingsgegevens."""

        self.base_url = (base_url or current_app.config["MM_API_BASE_URL"]).rstrip("/")
        self.language = language or current_app.config["MM_LANGUAGE"]
        self.dataset_spec = current_app.config.get(
            "MM_DATASET_SPEC", "enb-119-beeldmateriaal"
        )
        self.timeout_seconds = (
            timeout_seconds or current_app.config["MM_TIMEOUT_SECONDS"]
        )

    def get_record(self, mm_id: str) -> dict[str, Any]:
        """Haal één MM-record op via de stabiele hub-id."""

        try:
            return self._request_json(self._build_record_url(mm_id))
        except HTTPError as exc:
            if exc.code == 404:
                raise NotFoundError(
                    "Het Maior Memorix-record bestaat niet.",
                    code="MEMORIX_RECORD_NOT_FOUND",
                    details={"mm_id": mm_id},
                ) from exc
            raise ExternalServiceError(
                "Maior Memorix kon het record niet leveren.",
                code="MEMORIX_REQUEST_FAILED",
                details={"mm_id": mm_id, "status_code": exc.code},
            ) from exc
        except (TimeoutError, URLError) as exc:
            raise ExternalServiceError(
                "Maior Memorix is momenteel niet bereikbaar.",
                code="MEMORIX_UNAVAILABLE",
                details={"mm_id": mm_id},
            ) from exc
        except json.JSONDecodeError as exc:
            raise ExternalServiceError(
                "Maior Memorix gaf een ongeldig antwoord terug.",
                code="MEMORIX_INVALID_RESPONSE",
                details={"mm_id": mm_id},
            ) from exc

    def get_metadata_record(
        self,
        mm_id: str,
    ) -> tuple[dict[str, Any], MemorixMetadata]:
        """Geef actuele MM-velden en genormaliseerde metadata voor één record."""

        record = self.get_record(mm_id)
        fields = self._get_fields(record, mm_id)
        return fields, self.normalize_metadata_from_fields(fields)

    def get_photo_data(self, mm_id: str) -> dict[str, str]:
        """Geef de afbeelding en zichtbare bronmetadata van een MM-record."""

        record = self.get_record(mm_id)
        fields = self._get_fields(record, mm_id)
        metadata = self.normalize_metadata_from_fields(fields)
        return {
            "image_source": self._get_image_source(fields, mm_id),
            "subject": metadata.subject,
            "date": metadata.date,
            "location": metadata.location,
            "description": metadata.description,
            "description_raw": metadata.description_raw,
        }

    def get_landing_data(self, mm_id: str) -> dict[str, str]:
        """Geef miniatuur en lijstmetadata van een MM-record."""

        record = self.get_record(mm_id)
        fields = self._get_fields(record, mm_id)
        metadata = self.normalize_metadata_from_fields(fields)
        return {
            "thumbnail_url": self._get_thumbnail_url(fields),
            "subject": metadata.subject,
            "date": metadata.date,
            "location": metadata.location,
            "description": metadata.description,
            "description_raw": metadata.description_raw,
        }

    def get_landing_data_from_fields(self, fields: dict[str, Any]) -> dict[str, str]:
        """Geef lijstmetadata uit een eerder opgeslagen MM-veldenobject."""

        metadata = self.normalize_metadata_from_fields(fields)
        return {
            "thumbnail_url": self._get_thumbnail_url(fields),
            "subject": metadata.subject,
            "date": metadata.date,
            "location": metadata.location,
            "description": metadata.description,
            "description_raw": metadata.description_raw,
        }

    def normalize_metadata_from_fields(
        self,
        fields: dict[str, Any],
    ) -> MemorixMetadata:
        """Normaliseer MM-velden éénmalig naar de FNO-metadatavorm."""

        raw_description = self._get_first_value(fields, "dc_description")
        return MemorixMetadata(
            subject=self._get_first_value(
                fields, "dc_title", "dc_subject", "delving_title"
            ),
            date=self.format_date_range(fields),
            location=self._get_first_value(
                fields, "tib_place", "dcterms_spatial", "dc_coverage"
            ),
            description=self.clean_description(raw_description),
            description_raw=self.clean_description_lines(raw_description),
        )

    def get_local_metadata_from_fields(self, fields: dict[str, Any]) -> dict[str, str]:
        """Geef lokale FNO-metadata uit een MM-veldenobject."""

        return self.normalize_metadata_from_fields(fields).as_local_values()

    def get_image_source(self, mm_id: str) -> str:
        """Geef de Deep Zoom-bron van één MM-record terug."""

        return self.get_photo_data(mm_id)["image_source"]

    def get_detection_image(self, mm_id: str) -> bytes:
        """Download de publieke MM-thumbnail voor gezichtsdetectie."""

        record = self.get_record(mm_id)
        fields = self._get_fields(record, mm_id)
        return self.get_detection_image_from_fields(fields, mm_id)

    def get_detection_image_from_fields(
        self,
        fields: dict[str, Any],
        mm_id: str,
    ) -> bytes:
        """Download de detectieafbeelding uit reeds opgeslagen MM-velden."""

        image_url = self._get_thumbnail_url(fields)
        if not image_url:
            raise ExternalServiceError(
                "Het Maior Memorix-record bevat geen detectieafbeelding.",
                code="PERSON_DETECTION_IMAGE_MISSING",
                details={"mm_id": mm_id},
            )

        return self._download_cached_binary(
            image_url,
            self.timeout_seconds,
            mm_id,
        )

    @staticmethod
    @lru_cache(maxsize=128)
    def _download_cached_binary(
        url: str,
        timeout_seconds: float,
        mm_id: str,
    ) -> bytes:
        """Download en cache een kleine publieke detectieafbeelding."""

        try:
            request = Request(
                url,
                headers={"User-Agent": "Foto-Nummeraar-Online/1.0"},
            )
            with urlopen(request, timeout=timeout_seconds) as response:
                return response.read()
        except (HTTPError, TimeoutError, URLError) as exc:
            raise ExternalServiceError(
                "De foto kon niet voor gezichtsdetectie worden opgehaald.",
                code="PERSON_DETECTION_IMAGE_UNAVAILABLE",
                details={"mm_id": mm_id},
            ) from exc

    def _download_binary(self, url: str, mm_id: str) -> bytes:
        """Download binaire brondata met uniforme foutafhandeling."""

        try:
            request = Request(
                url,
                headers={"User-Agent": "Foto-Nummeraar-Online/1.0"},
            )
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return response.read()
        except (HTTPError, TimeoutError, URLError) as exc:
            raise ExternalServiceError(
                "De foto kon niet voor gezichtsdetectie worden opgehaald.",
                code="PERSON_DETECTION_IMAGE_UNAVAILABLE",
                details={"mm_id": mm_id},
            ) from exc

    @staticmethod
    def _get_fields(record: dict[str, Any], mm_id: str) -> dict[str, Any]:
        """Haal het veldenobject uit een MM-record."""

        try:
            fields = record["result"]["item"]["fields"]
        except (KeyError, TypeError) as exc:
            raise ExternalServiceError(
                "Het Maior Memorix-record bevat geen geldige velden.",
                code="MEMORIX_FIELDS_MISSING",
                details={"mm_id": mm_id},
            ) from exc

        if not isinstance(fields, dict):
            raise ExternalServiceError(
                "Het Maior Memorix-record bevat geen geldige velden.",
                code="MEMORIX_FIELDS_INVALID",
                details={"mm_id": mm_id},
            )

        return fields

    @classmethod
    def format_date_range(cls, fields: dict[str, Any]) -> str:
        """Formatteer MM-begin- en einddatering als één leesbare waarde."""

        start = cls._get_first_value(fields, "tib_productionStart")
        end = cls._get_first_value(fields, "tib_productionEnd")
        if start and end and start != end:
            return f"{start} / {end}"
        return (
            start
            or end
            or cls._get_first_value(fields, "dcterms_created", "tib_date", "dc_date")
        )

    @staticmethod
    def clean_description(value: str) -> str:
        """Verwijder eenvoudige HTML-opmaak uit MM-beschrijvingen."""

        return " ".join(MemorixService.clean_description_lines(value).split())

    @staticmethod
    def clean_description_lines(value: str) -> str:
        """Reinig MM-tekst met behoud van regeleinden voor de parser."""

        text = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
        text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return unescape(text).replace("\r\n", "\n").replace("\r", "\n").strip()

    @classmethod
    def _get_thumbnail_url(cls, fields: dict[str, Any]) -> str:
        """Geef de eerste beschikbare MM-miniatuur-URL."""

        return cls._get_first_value(
            fields,
            "delving_thumbnail",
            "delving_preview",
            "delving_imageUrl",
            "europeana_object",
            "edm_object",
        )

    @staticmethod
    def _get_image_source(fields: dict[str, Any], mm_id: str) -> str:
        """Haal de Deep Zoom-bron uit MM-velden."""

        try:
            image_source = fields["delving_deepZoomUrl"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise ExternalServiceError(
                "Het Maior Memorix-record bevat geen Deep Zoom-afbeelding.",
                code="MEMORIX_IMAGE_SOURCE_MISSING",
                details={"mm_id": mm_id},
            ) from exc

        if not isinstance(image_source, str) or not image_source.strip():
            raise ExternalServiceError(
                "Het Maior Memorix-record bevat geen geldige Deep Zoom-afbeelding.",
                code="MEMORIX_IMAGE_SOURCE_INVALID",
                details={"mm_id": mm_id},
            )

        return image_source

    @staticmethod
    def _get_first_value(fields: dict[str, Any], *keys: str) -> str:
        """Geef de eerste bruikbare tekstwaarde uit een reeks MM-velden."""

        for key in keys:
            value = fields.get(key)
            if isinstance(value, list):
                parts = [str(item).strip() for item in value if str(item).strip()]
                if parts:
                    return "; ".join(parts)
            elif value is not None and str(value).strip():
                return str(value).strip()

        return ""

    def _build_record_url(self, mm_id: str) -> str:
        """Bouw de API-URL voor één MM-record."""

        encoded_mm_id = quote(mm_id, safe="")
        query = urlencode({
            "format": "json",
            "lang": self.language,
        })

        return f"{self.base_url}/search/v1/{encoded_mm_id}/?{query}"

    def get_facet_values(self, field: str) -> list[str]:
        """Geef gecachte waarden voor één BrabantCloud-facet."""

        return list(
            self._get_facet_values_cached(
                self.base_url,
                self.language,
                self.dataset_spec,
                self.timeout_seconds,
                field,
            )
        )

    @staticmethod
    @lru_cache(maxsize=64)
    def _get_facet_values_cached(
        base_url: str,
        language: str,
        dataset_spec: str,
        timeout_seconds: float,
        field: str,
    ) -> tuple[str, ...]:
        """Haal facetwaarden op en cache ze voor volgende beheerrequests."""

        query_items: list[tuple[str, str]] = [
            ("format", "json"),
            ("lang", language),
            ("query", "*:*"),
            ("rows", "0"),
            ("hqf[]", f"delving_spec:{dataset_spec}"),
            ("facet.full", f"{field}.raw"),
        ]
        request = Request(
            f"{base_url}/search/v1/?{urlencode(query_items)}",
            headers={
                "Accept": "application/json",
                "User-Agent": "Foto-Nummeraar-Online/1.0",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read().decode("utf-8")
            data = MemorixService._decode_json_payload(payload)
        except (HTTPError, TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise ExternalServiceError(
                "Maior Memorix kon de filteropties niet leveren.",
                code="MEMORIX_FACETS_FAILED",
                details={"field": field},
            ) from exc

        return tuple(
            sorted(MemorixService._extract_facet_values(data), key=str.casefold)
        )

    @classmethod
    def _extract_facet_values(cls, payload: object) -> list[str]:
        """Vind facetwaarden in verschillende BrabantCloud-responsvormen."""

        values: set[str] = set()

        def visit(value: object, *, in_facet: bool = False) -> None:
            if isinstance(value, dict):
                facet_context = in_facet or any(
                    key in value
                    for key in ("facets", "facet", "facetFields", "facet_counts")
                )
                for key, item in value.items():
                    if facet_context and key in ("value", "label", "name", "term"):
                        if isinstance(item, str) and item.strip():
                            values.add(item.strip())
                    visit(item, in_facet=facet_context or "facet" in key.lower())
            elif isinstance(value, list):
                if in_facet:
                    for index in range(0, len(value) - 1, 2):
                        if isinstance(value[index], str) and isinstance(
                            value[index + 1], int
                        ):
                            values.add(value[index].strip())
                for item in value:
                    visit(item, in_facet=in_facet)

        visit(payload)
        return [value for value in values if value]

    def _request_json(self, url: str) -> dict[str, Any]:
        """Voer één BrabantCloud-aanvraag uit en decodeer JSON of JSONP."""

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Foto-Nummeraar-Online/1.0",
            },
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        return self._decode_json_payload(payload)

    @staticmethod
    def _decode_json_payload(payload: str) -> dict[str, Any]:
        """Decodeer JSON en JSONP van BrabantCloud."""

        text = payload.strip()
        if not text.startswith("{"):
            start = text.find("(")
            end = text.rfind(")")
            if start == -1 or end <= start:
                raise json.JSONDecodeError("Ongeldige JSONP", text, 0)
            text = text[start + 1 : end].strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            raise json.JSONDecodeError("JSON-object verwacht", text, 0)
        return data

    def search_records(
        self,
        *,
        filters: dict[str, str],
        rows: int = 100,
    ) -> list[dict[str, Any]]:
        """Zoek alle MM-records die aan de opgegeven filters voldoen."""

        start = 0
        records: list[dict[str, Any]] = []

        while True:
            page = self._search_page(filters=filters, start=start, rows=rows)
            items = self._get_search_items(page)
            records.extend(items)

            if len(items) < rows:
                break

            start += rows

        return records

    def search_records_page(
        self,
        *,
        filters: dict[str, str],
        page: int,
        page_size: int = 100,
    ) -> tuple[list[dict[str, Any]], int]:
        """Haal één pagina MM-zoekresultaten en het totale aantal op."""

        safe_page = max(page, 1)
        safe_page_size = max(page_size, 1)
        start = (safe_page - 1) * safe_page_size
        payload = self._search_page(
            filters=filters,
            start=start,
            rows=safe_page_size,
        )
        return self._get_search_items(payload), self._get_search_total(payload)

    def _search_page(
        self,
        *,
        filters: dict[str, str],
        start: int,
        rows: int,
    ) -> dict[str, Any]:
        """Haal één pagina zoekresultaten uit BrabantCloud op."""

        query_items: list[tuple[str, str | int]] = [
            ("format", "json"),
            ("lang", self.language),
            ("query", "*:*"),
            ("start", start),
            ("rows", rows),
            ("hqf[]", f"delving_spec:{self.dataset_spec}"),
        ]
        query_items.extend(
            ("qf[]", f"{field}:{value.strip()}")
            for field, value in filters.items()
            if value.strip()
        )
        try:
            data = self._request_json(
                f"{self.base_url}/search/v1/?{urlencode(query_items)}"
            )
        except (HTTPError, TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise ExternalServiceError(
                "Maior Memorix kon de zoekopdracht niet uitvoeren.",
                code="MEMORIX_SEARCH_FAILED",
                details={"filters": filters},
            ) from exc

        if not isinstance(data, dict):
            raise ExternalServiceError(
                "Maior Memorix gaf ongeldige zoekresultaten terug.",
                code="MEMORIX_INVALID_SEARCH_RESPONSE",
            )

        return data

    @staticmethod
    def _get_search_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Haal zoekitems uit bekende BrabantCloud-responsvormen."""

        candidates = (
            payload.get("items"),
            payload.get("result", {}).get("items")
            if isinstance(payload.get("result"), dict)
            else None,
            payload.get("result", {}).get("item")
            if isinstance(payload.get("result"), dict)
            else None,
        )
        for candidate in candidates:
            if isinstance(candidate, list):
                return [item for item in candidate if isinstance(item, dict)]

        return []

    @staticmethod
    def _get_search_total(payload: dict[str, Any]) -> int:
        """Haal het totale aantal zoekresultaten uit bekende responsvormen."""

        containers = [payload]
        result = payload.get("result")
        if isinstance(result, dict):
            containers.append(result)

        candidates: list[object] = []
        for container in containers:
            candidates.extend([
                container.get("numFound"),
                container.get("@numFound"),
                container.get("total"),
            ])

            pagination = container.get("pagination")
            if isinstance(pagination, dict):
                candidates.extend([
                    pagination.get("numFound"),
                    pagination.get("@numFound"),
                    pagination.get("total"),
                ])

            query = container.get("query")
            if isinstance(query, dict):
                candidates.extend([
                    query.get("numFound"),
                    query.get("@numFound"),
                ])

        for value in candidates:
            if isinstance(value, int) and value >= 0:
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

        return len(MemorixService._get_search_items(payload))

    @classmethod
    def normalize_search_record(cls, record: dict[str, Any]) -> dict[str, Any]:
        """Normaliseer één BrabantCloud-zoekresultaat voor FNO."""

        payload = record
        nested_item = payload.get("item")
        if isinstance(nested_item, dict):
            payload = nested_item

        fields = payload.get("fields", payload)
        if not isinstance(fields, dict):
            fields = {}

        mm_id = cls._get_first_value(fields, "delving_hubId", "delving_pmhId")
        photo_number = cls._get_first_value(fields, "dc_identifier")
        return {
            "mm_id": mm_id,
            "photo_number": photo_number,
            "title": cls._get_first_value(fields, "dc_title", "delving_title"),
            "date": cls._get_first_value(fields, "dcterms_created", "tib_date"),
            "location": cls._get_first_value(fields, "tib_place", "dcterms_spatial"),
            "collection_part": cls._get_first_value(fields, "tib_collectionPart"),
            "subject": cls._get_first_value(fields, "dc_subject"),
            "thumbnail_url": cls._get_thumbnail_url(fields),
            "fields": fields,
        }
