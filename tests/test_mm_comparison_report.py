"""Tests voor het read-only MM-vergelijkrapport."""

from io import BytesIO
from types import SimpleNamespace

from openpyxl import load_workbook

from app.models import Photo
from app.services.memorix_service import MemorixMetadata
from app.services.mm_comparison_report_service import MmComparisonReportService


class PhotoRepositoryStub:
    """Lever vaste foto's zonder databasewijzigingen."""

    def __init__(self, photos: list[Photo]) -> None:
        self.photos = photos

    def get_all(self) -> list[Photo]:
        """Geef alle testfoto's terug."""

        return self.photos


class PersonRepositoryStub:
    """Lever vaste personen per foto."""

    def __init__(self, persons: list[object]) -> None:
        self.persons = persons

    def get_by_photo(self, photo_id: int) -> list[object]:
        """Geef de testpersonen terug."""

        return self.persons


class MemorixServiceStub:
    """Lever actuele MM-data zonder externe requests."""

    def get_metadata_record(
        self, mm_id: str
    ) -> tuple[dict[str, object], MemorixMetadata]:
        """Geef één vast MM-record terug."""

        return (
            {"delving_landingPage": ["https://example.test/mm/MM-1"]},
            MemorixMetadata(
                subject="MM onderwerp",
                date="1939",
                location="Vortum-Mullem",
                description="Groepsfoto.",
                description_raw="Groepsfoto.\n1. Jan Jansen",
            ),
        )


class ParserStub:
    """Lever een betrouwbare parseruitkomst."""

    def parse(self, description: str) -> object:
        """Geef beschrijving en één genummerde naam terug."""

        return SimpleNamespace(
            description="Groepsfoto.",
            names={1: "Jan Jansen"},
            reliable=True,
            reason=None,
        )


def build_photo() -> Photo:
    """Maak een geïmporteerde numbered-mode foto met lokale metadata."""

    photo = Photo(
        mm_id="MM-1",
        photo_number="A001",
        local_subject="FNO onderwerp",
        local_date="1939",
        local_location="Vortum-Mullem",
        local_description="Groepsfoto.",
        person_display_mode="numbered",
    )
    photo.id = 1
    return photo


def test_report_contains_only_actionable_differences_and_mm_link() -> None:
    """Gelijke velden verdwijnen en verschillen krijgen een klikbare MM-link."""

    service = MmComparisonReportService(
        photo_repository=PhotoRepositoryStub([build_photo()]),
        person_repository=PersonRepositoryStub([
            SimpleNamespace(label_number=1, current_name="Jan Jansen")
        ]),
        memorix_service=MemorixServiceStub(),
        description_parser=ParserStub(),
    )

    rows = service.build_rows()

    assert [(row.field, row.fno_value, row.mm_value) for row in rows] == [
        ("Onderwerp", "FNO onderwerp", "MM onderwerp")
    ]
    assert rows[0].mm_url == "https://example.test/mm/MM-1"

    workbook = load_workbook(BytesIO(service.build_xlsx()))
    sheet = workbook["Actiepunten"]
    assert sheet["A2"].value == "A001"
    assert sheet["D2"].value == "Onderwerp"
    assert sheet["G2"].hyperlink.target == "https://example.test/mm/MM-1"


def test_numbered_mode_does_not_add_unimported_mm_photo() -> None:
    """Numbered-mode voegt geen niet-geïmporteerde n-variant toe aan het rapport."""

    service = MmComparisonReportService(
        photo_repository=PhotoRepositoryStub([build_photo()]),
        person_repository=PersonRepositoryStub([
            SimpleNamespace(label_number=1, current_name="Jan Jansen")
        ]),
        memorix_service=MemorixServiceStub(),
        description_parser=ParserStub(),
    )

    rows = service.build_rows()

    assert all(row.photo_number == "A001" for row in rows)
    assert all(row.field != "MM-foto" for row in rows)
