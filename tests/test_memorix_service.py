"""Tests voor MemorixService."""

import json
from urllib.error import HTTPError, URLError

import pytest

from app.exceptions import ExternalServiceError, NotFoundError
from app.services import MemorixService


class FakeResponse:
    """Eenvoudig HTTP-responseobject voor tests."""

    def __init__(self, payload: dict | list | str) -> None:
        if isinstance(payload, str):
            self.payload = payload.encode("utf-8")
        else:
            self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def create_record(*, image_source: str | None = "https://example.test/photo.dzi"):
    """Maak een minimale MM-response."""

    fields = {}

    if image_source is not None:
        fields["delving_deepZoomUrl"] = [image_source]

    return {
        "result": {
            "item": {
                "fields": fields,
            }
        }
    }


def test_get_image_source_returns_deep_zoom_url(app, monkeypatch) -> None:
    """De Deep Zoom-URL wordt uit het MM-record gehaald."""

    def fake_urlopen(request, timeout):
        assert request.full_url == (
            "https://data.example.test/api/search/v1/MM-RECORD-001/?format=json&lang=nl"
        )
        assert timeout == 5
        return FakeResponse(create_record())

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )

    service = MemorixService(
        base_url="https://data.example.test/api/",
        language="nl",
        timeout_seconds=5,
    )

    assert service.get_image_source("MM-RECORD-001") == (
        "https://example.test/photo.dzi"
    )


def test_get_photo_data_returns_visible_metadata(app, monkeypatch) -> None:
    """Zichtbare metadata wordt uit bekende MM-velden gehaald."""

    record = create_record()
    fields = record["result"]["item"]["fields"]
    fields.update({
        "dc_title": ["Groepsfoto"],
        "dc_date": ["1954"],
        "dc_coverage": ["Vortum-Mullem"],
    })
    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        lambda request, timeout: FakeResponse(record),
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    assert service.get_photo_data("MM-001") == {
        "image_source": "https://example.test/photo.dzi",
        "subject": "Groepsfoto",
        "date": "1954",
        "location": "Vortum-Mullem",
        "description": "",
        "description_raw": "",
    }


def test_record_id_is_url_encoded(app, monkeypatch) -> None:
    """Speciale tekens in een MM-id worden veilig gecodeerd."""

    captured_url = None

    def fake_urlopen(request, timeout):
        nonlocal captured_url
        captured_url = request.full_url
        return FakeResponse(create_record())

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        language="nl",
        timeout_seconds=5,
    )

    service.get_record("record met/spatie")

    assert captured_url == (
        "https://data.example.test/api/search/v1/record%20met%2Fspatie/"
        "?format=json&lang=nl"
    )


def test_unknown_memorix_record_raises_not_found(app, monkeypatch) -> None:
    """Een HTTP 404 wordt vertaald naar een domeinfout."""

    def fake_urlopen(request, timeout):
        raise HTTPError(
            request.full_url,
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    with pytest.raises(NotFoundError) as exc:
        service.get_record("UNKNOWN")

    assert exc.value.code == "MEMORIX_RECORD_NOT_FOUND"
    assert exc.value.details == {"mm_id": "UNKNOWN"}


def test_unavailable_memorix_raises_external_service_error(
    app,
    monkeypatch,
) -> None:
    """Netwerkfouten worden vertaald naar een externe-servicefout."""

    def fake_urlopen(request, timeout):
        raise URLError("connection failed")

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    with pytest.raises(ExternalServiceError) as exc:
        service.get_record("MM-001")

    assert exc.value.code == "MEMORIX_UNAVAILABLE"
    assert exc.value.details == {"mm_id": "MM-001"}


def test_invalid_json_raises_external_service_error(app, monkeypatch) -> None:
    """Ongeldige JSON wordt gecontroleerd afgehandeld."""

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        lambda request, timeout: FakeResponse("not-json"),
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    with pytest.raises(ExternalServiceError) as exc:
        service.get_record("MM-001")

    assert exc.value.code == "MEMORIX_INVALID_RESPONSE"


def test_missing_image_source_raises_external_service_error(
    app,
    monkeypatch,
) -> None:
    """Een record zonder Deep Zoom-bron geeft een duidelijke fout."""

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        lambda request, timeout: FakeResponse(create_record(image_source=None)),
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    with pytest.raises(ExternalServiceError) as exc:
        service.get_image_source("MM-001")

    assert exc.value.code == "MEMORIX_IMAGE_SOURCE_MISSING"
    assert exc.value.details == {"mm_id": "MM-001"}


def test_get_landing_data_returns_thumbnail_and_metadata(app, monkeypatch) -> None:
    """De landingspagina ontvangt miniatuur en zichtbare lijstmetadata."""

    record = create_record()
    fields = record["result"]["item"]["fields"]
    fields.update({
        "delving_thumbnail": ["https://example.test/thumb.jpg"],
        "dc_title": ["Dorpsfeest"],
        "dc_date": ["1968"],
        "dc_coverage": ["Boxmeer"],
    })
    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        lambda request, timeout: FakeResponse(record),
    )

    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    assert service.get_landing_data("MM-001") == {
        "thumbnail_url": "https://example.test/thumb.jpg",
        "subject": "Dorpsfeest",
        "date": "1968",
        "location": "Boxmeer",
        "description": "",
        "description_raw": "",
    }


def test_search_uses_unquoted_facet_value(app, monkeypatch) -> None:
    """Een facetwaarde wordt op het geïndexeerde MM-veld gefilterd."""

    captured_url = ""

    def fake_urlopen(request, timeout):
        nonlocal captured_url
        captured_url = request.full_url
        return FakeResponse({"result": {"items": []}})

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )
    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    service.search_records(
        filters={"tib_collectionPart_facet": "Vortum-Mullem"},
    )

    assert "qf%5B%5D=tib_collectionPart_facet%3AVortum-Mullem" in captured_url
    assert "%22Vortum-Mullem%22" not in captured_url


def test_normalize_search_record_unwraps_nested_item() -> None:
    """Een zoekrecord met item-wrapper wordt correct genormaliseerd."""

    record = {
        "item": {
            "fields": {
                "delving_hubId": ["MM-001"],
                "dc_identifier": ["A19011"],
                "dc_title": ["Priesterwijding P. Stevens"],
                "dcterms_created": ["1939"],
                "tib_place": ["Vortum-Mullem"],
                "tib_collectionPart": ["Vortum-Mullem"],
                "dc_subject": ["Personen", "Religie"],
            }
        }
    }

    normalized = MemorixService.normalize_search_record(record)

    assert normalized["mm_id"] == "MM-001"
    assert normalized["photo_number"] == "A19011"
    assert normalized["title"] == "Priesterwijding P. Stevens"
    assert normalized["date"] == "1939"
    assert normalized["location"] == "Vortum-Mullem"
    assert normalized["collection_part"] == "Vortum-Mullem"
    assert normalized["subject"] == "Personen; Religie"


def test_get_detection_image_downloads_public_thumbnail(app, monkeypatch) -> None:
    """Gezichtsdetectie gebruikt de publieke MM-thumbnail in één aanvraag."""

    record = create_record()
    fields = record["result"]["item"]["fields"]
    fields["delving_thumbnail"] = ["https://images.example.test/thumb.jpg"]
    calls: list[str] = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if request.full_url.startswith("https://data.example.test"):
            return FakeResponse(record)
        assert timeout == 5
        return FakeResponse("thumbnail-bytes")

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )
    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    result = service.get_detection_image("MM-001")

    assert result == b"thumbnail-bytes"
    assert calls[-1] == "https://images.example.test/thumb.jpg"


def test_search_records_page_uses_offset_and_total(app, monkeypatch) -> None:
    """Paginering gebruikt één MM-aanvraag met de juiste offset."""

    captured_url = ""

    def fake_urlopen(request, timeout):
        nonlocal captured_url
        captured_url = request.full_url
        return FakeResponse({
            "result": {
                "numFound": 250,
                "items": [{"fields": {"dc_identifier": ["A19011"]}}],
            }
        })

    monkeypatch.setattr(
        "app.services.memorix_service.urlopen",
        fake_urlopen,
    )
    service = MemorixService(
        base_url="https://data.example.test/api",
        timeout_seconds=5,
    )

    records, total = service.search_records_page(
        filters={"tib_collectionPart_facet": "Vortum-Mullem"},
        page=2,
        page_size=100,
    )

    assert len(records) == 1
    assert total == 250
    assert "start=100" in captured_url
    assert "rows=100" in captured_url


def test_get_search_total_reads_pagination_num_found() -> None:
    """Het MM-totaal wordt uit de pagination-sectie gelezen."""

    payload = {
        "pagination": {"start": 0, "rows": 100, "numFound": 780},
        "items": [{"fields": {}} for _ in range(100)],
    }

    assert MemorixService._get_search_total(payload) == 780


def test_get_search_total_reads_nested_pagination_num_found() -> None:
    """Ook een geneste MM-resultaatwrapper levert het volledige totaal."""

    payload = {
        "result": {
            "pagination": {"numFound": "780"},
            "items": [{"fields": {}} for _ in range(100)],
        }
    }

    assert MemorixService._get_search_total(payload) == 780
