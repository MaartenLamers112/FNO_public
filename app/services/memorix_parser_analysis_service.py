"""Read-only analyse van MM-beschrijvingen voor parserverbetering."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.memorix_description_parser import MemorixDescriptionParser
from app.services.memorix_service import MemorixService
from app.services.mm_import_service import FILTER_FIELDS


@dataclass(frozen=True, slots=True)
class MemorixParserAnalysisRow:
    """Analyse-uitkomst voor één MM-record."""

    mm_id: str
    photo_number: str
    category: str
    reliable: bool
    reason: str
    pattern_group: str
    numbered_items_count: int
    candidate_items: str
    unknown_positions_count: int
    list_layout: str
    has_name_header: bool
    warning_signals: str
    names_count: int
    names: str
    parsed_description: str
    original_description: str


class MemorixParserAnalysisService:
    """Classificeer MM-beschrijvingen zonder gegevens te wijzigen."""

    _numbered_line = re.compile(r"(?m)^\s*\d+[.)]\s*\S+")
    _header_line = re.compile(
        r"(?im)^\s*(namen|namenlijst|personen|wie is wie)\s*:?\s*$"
    )
    _numbered_item = re.compile(
        r"(?<!\w)(?P<number>\d{1,3})\s*[.):]\s*"
        r"(?P<value>.*?)(?=(?<!\w)\d{1,3}\s*[.):]\s*|$)",
        re.DOTALL,
    )
    _unknown_value = re.compile(
        r"(?i)^(?:[.\-?_/ ]{2,}|onbekend|onbekende|niet bekend|n\.?n\.?|"
        r"naam onbekend)$"
    )

    def __init__(
        self,
        *,
        memorix_service: MemorixService | None = None,
        parser: MemorixDescriptionParser | None = None,
    ) -> None:
        self.memorix_service = memorix_service or MemorixService()
        self.parser = parser or MemorixDescriptionParser()

    def analyze(self, filters: dict[str, str]) -> list[MemorixParserAnalysisRow]:
        """Analyseer alle MM-records binnen de opgegeven importfilters."""

        mm_filters = self._normalize_filters(filters)
        rows: list[MemorixParserAnalysisRow] = []

        for raw_record in self.memorix_service.search_records(
            filters=mm_filters,
            rows=1000,
        ):
            record = self.memorix_service.normalize_search_record(raw_record)
            fields = record["fields"]
            metadata = self.memorix_service.normalize_metadata_from_fields(fields)
            original_description = metadata.description_raw
            parse_result = self.parser.parse(original_description)
            items = self._extract_numbered_items(original_description)
            has_name_header = bool(self._header_line.search(original_description))
            list_layout = self._list_layout(original_description, items)
            unknown_positions_count = sum(self._is_unknown(value) for _, value in items)
            pattern_group = self._pattern_group(
                original_description,
                items=items,
                has_name_header=has_name_header,
                unknown_positions_count=unknown_positions_count,
            )
            warning_signals = self._warning_signals(items)

            rows.append(
                MemorixParserAnalysisRow(
                    mm_id=record["mm_id"],
                    photo_number=record["photo_number"],
                    category=self._classify(
                        original_description,
                        parse_result.reliable,
                    ),
                    reliable=parse_result.reliable,
                    reason=parse_result.reason or "",
                    pattern_group=pattern_group,
                    numbered_items_count=len(items),
                    candidate_items=" | ".join(
                        f"{number}. {value}" for number, value in items
                    ),
                    unknown_positions_count=unknown_positions_count,
                    list_layout=list_layout,
                    has_name_header=has_name_header,
                    warning_signals=warning_signals,
                    names_count=len(parse_result.names),
                    names=" | ".join(
                        f"{number}. {name}"
                        for number, name in parse_result.names.items()
                    ),
                    parsed_description=parse_result.description,
                    original_description=original_description,
                )
            )

        priority = {
            "twijfelachtig": 0,
            "geen_herkenbaar_patroon": 1,
            "betrouwbaar": 2,
            "lege_beschrijving": 3,
        }
        return sorted(
            rows,
            key=lambda row: (
                priority[row.category],
                row.pattern_group,
                row.photo_number.casefold(),
                row.mm_id.casefold(),
            ),
        )

    def _classify(self, description: str, reliable: bool) -> str:
        """Classificeer zonder te gokken of vrije tekst personen bevat."""

        if not description.strip():
            return "lege_beschrijving"
        if reliable:
            return "betrouwbaar"
        if self._numbered_line.search(description) or self._header_line.search(
            description
        ):
            return "twijfelachtig"
        return "geen_herkenbaar_patroon"

    def _extract_numbered_items(self, description: str) -> list[tuple[int, str]]:
        """Haal mogelijke genummerde lijstitems uit vrije tekst."""

        if not description.strip():
            return []

        normalized = re.sub(r"[\t\r]+", " ", description)
        items: list[tuple[int, str]] = []
        for match in self._numbered_item.finditer(normalized):
            value = " ".join(match.group("value").split()).strip(" ,;")
            if value:
                items.append((int(match.group("number")), value))
        return items

    @staticmethod
    def _list_layout(
        description: str,
        items: list[tuple[int, str]],
    ) -> str:
        """Beschrijf of kandidaten op één of meerdere regels staan."""

        if not items:
            return "geen"
        numbered_lines = [
            line
            for line in description.splitlines()
            if re.search(r"(?<!\w)\d{1,3}\s*[.):]\s*\S+", line)
        ]
        if len(numbered_lines) >= 2:
            return "meerdere_regels"
        return "een_regel"

    def _pattern_group(
        self,
        description: str,
        *,
        items: list[tuple[int, str]],
        has_name_header: bool,
        unknown_positions_count: int,
    ) -> str:
        """Groepeer structurele patronen zonder importbeslissing te nemen."""

        if not description.strip():
            return "P0_lege_beschrijving"
        if not items:
            if has_name_header:
                return "P5_namenkop_zonder_nummerlijst"
            return "P6_vrije_tekst_zonder_nummerlijst"

        layout = self._list_layout(description, items)
        if unknown_positions_count:
            return "P3_nummerlijst_met_onbekende_posities"
        if has_name_header:
            return "P1_namenkop_met_nummerlijst"
        if layout == "meerdere_regels":
            return "P2_nummerlijst_meerdere_regels"
        return "P4_nummerlijst_een_regel"

    def _warning_signals(self, items: list[tuple[int, str]]) -> str:
        """Signaleer structuurrisico's zonder inhoud als persoon te beoordelen."""

        if not items:
            return ""

        warnings: list[str] = []
        numbers = [number for number, _ in items]
        if numbers[0] != 1:
            warnings.append("start_niet_bij_1")
        if any(
            current != previous + 1
            for previous, current in zip(numbers, numbers[1:], strict=False)
        ):
            warnings.append("nummering_niet_aaneengesloten")
        if len(set(numbers)) != len(numbers):
            warnings.append("dubbele_nummers")
        if any(len(value) > 120 for _, value in items):
            warnings.append("zeer_lang_lijstitem")
        if any(self._is_unknown(value) for _, value in items):
            warnings.append("onbekende_posities")
        return " | ".join(warnings)

    def _is_unknown(self, value: str) -> bool:
        """Herken expliciete lege of onbekende posities."""

        return bool(self._unknown_value.fullmatch(value.strip()))

    @staticmethod
    def _normalize_filters(filters: dict[str, str]) -> dict[str, str]:
        """Vertaal dezelfde beheerfilters als de MM-import."""

        return {
            FILTER_FIELDS[key]: value.strip()
            for key, value in filters.items()
            if key in FILTER_FIELDS and value.strip()
        }
