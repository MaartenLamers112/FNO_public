"""Tests voor de read-only MM-parseranalyse."""

from app.extensions import db
from app.models import Role, User
from app.services import MemorixParserAnalysisService
from app.services.memorix_service import MemorixMetadata, MemorixService


class FakeMemorixService:
    """Lever vaste MM-records zonder netwerkverkeer."""

    def __init__(self, records: list[dict[str, object]]) -> None:
        self.records = records
        self.received_filters: dict[str, str] | None = None
        self.received_rows: int | None = None

    def search_records(self, *, filters, rows=100):
        """Geef de ingestelde testrecords terug."""

        self.received_filters = filters
        self.received_rows = rows
        return self.records

    def normalize_search_record(self, record):
        """Gebruik dezelfde normalisatie als de echte service."""

        return MemorixService.normalize_search_record(record)

    def normalize_metadata_from_fields(self, fields):
        """Normaliseer alleen de beschrijving die voor deze test nodig is."""

        raw = MemorixService._get_first_value(fields, "dc_description")
        cleaned = MemorixService.clean_description_lines(raw)
        return MemorixMetadata(
            subject="",
            date="",
            location="",
            description=MemorixService.clean_description(raw),
            description_raw=cleaned,
        )


def record(mm_id: str, photo_number: str, description: str) -> dict[str, object]:
    """Maak een minimaal MM-zoekrecord voor parseranalyse."""

    return {
        "fields": {
            "delving_hubId": [mm_id],
            "dc_identifier": [photo_number],
            "dc_description": [description],
        }
    }


def test_parser_analysis_classifies_and_groups_patterns() -> None:
    """Analyse onderscheidt parseruitkomsten en structurele patronen."""

    memorix = FakeMemorixService([
        record(
            "MM-1",
            "A001",
            "Groepsfoto.\n\nNamen:\n1. Jan Jansen\n2. Piet Peters",
        ),
        record("MM-2", "A002", "1. Jan Jansen, 2. ......., 3. Piet Peters"),
        record("MM-3", "A003", "1. Eerste onderdeel\n2. Tweede onderdeel"),
        record("MM-4", "A004", "Een gewone beschrijving zonder nummering."),
        record("MM-5", "A005", ""),
    ])
    service = MemorixParserAnalysisService(memorix_service=memorix)

    rows = service.analyze({"collection_part": "Vortum-Mullem"})

    assert memorix.received_filters == {"tib_collectionPart_facet": "Vortum-Mullem"}
    assert memorix.received_rows == 1000

    by_number = {row.photo_number: row for row in rows}
    assert by_number["A001"].pattern_group == "P1_namenkop_met_nummerlijst"
    assert by_number["A001"].numbered_items_count == 2
    assert by_number["A001"].list_layout == "meerdere_regels"
    assert by_number["A001"].has_name_header is True

    assert by_number["A002"].pattern_group == "P3_nummerlijst_met_onbekende_posities"
    assert by_number["A002"].unknown_positions_count == 1
    assert "onbekende_posities" in by_number["A002"].warning_signals

    assert by_number["A003"].pattern_group == "P2_nummerlijst_meerdere_regels"
    assert by_number["A004"].pattern_group == "P6_vrije_tekst_zonder_nummerlijst"
    assert by_number["A005"].pattern_group == "P0_lege_beschrijving"


def create_admin() -> None:
    """Maak een beheerder voor de webtest."""

    role = Role(name="administrator", description="administrator")
    user = User(username="beheerder", role=role)
    user.set_password("test")
    db.session.add(user)
    db.session.commit()


def test_administrator_can_download_parser_analysis(app, client, monkeypatch) -> None:
    """Beheerder kan een uitgebreid CSV-analyserapport downloaden."""

    with app.app_context():
        create_admin()

    client.post("/login", data={"username": "beheerder", "password": "test"})

    monkeypatch.setattr(
        "app.core.routes.MemorixParserAnalysisService.analyze",
        lambda self, filters: [
            type(
                "AnalysisRow",
                (),
                {
                    "category": "betrouwbaar",
                    "reliable": True,
                    "reason": "",
                    "pattern_group": "P1_namenkop_met_nummerlijst",
                    "numbered_items_count": 2,
                    "candidate_items": "1. Jan Jansen | 2. Piet Peters",
                    "unknown_positions_count": 0,
                    "list_layout": "meerdere_regels",
                    "has_name_header": True,
                    "warning_signals": "",
                    "mm_id": "MM-1",
                    "photo_number": "A001",
                    "names_count": 2,
                    "names": "1. Jan Jansen | 2. Piet Peters",
                    "parsed_description": "Groepsfoto.",
                    "original_description": (
                        "Groepsfoto.\n\nNamen:\n1. Jan Jansen\n2. Piet Peters"
                    ),
                },
            )()
        ],
    )

    response = client.post(
        "/admin/photos/import",
        data={"action": "parser_analysis", "collection_part": "Vortum-Mullem"},
    )

    assert response.status_code == 200
    assert response.content_type.startswith("text/csv")
    assert "mm_parseranalyse_" in response.headers["Content-Disposition"]
    text = response.get_data(as_text=True)
    assert "Patroongroep;Aantal genummerde items;Kandidaat-items" in text
    assert "P1_namenkop_met_nummerlijst;2" in text
    assert "Jan Jansen" in text
