"""Parser voor MM-beschrijvingen met een genummerde namenlijst."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemorixDescriptionParseResult:
    """Resultaat van het splitsen van beschrijving en namenlijst."""

    description: str
    names: dict[int, str]
    reliable: bool
    reason: str | None = None


class MemorixDescriptionParser:
    """Splits alleen een aantoonbaar betrouwbare namenlijst af."""

    _name_line = re.compile(r"^\s*(\d+)[.)]\s*(.+?)\s*$")
    _colon_item = re.compile(r"(?<!\S)(\d{1,3}):\s*(.*?)(?=(?<!\S)\d{1,3}:\s*|$)")
    _compact_dot_item = re.compile(
        r"(?:^|,\s*)(\d{1,3})\.\s*(.*?)(?=,\s*\d{1,3}\.\s*|$)"
    )
    _unknown_name = re.compile(r"^(?:\?+|[.…]{2,}|[-_/]{2,})$")
    _header_line = re.compile(
        r"^\s*(namen|namenlijst|personen|wie is wie)\s*:?\s*$",
        re.IGNORECASE,
    )

    def parse(self, value: str) -> MemorixDescriptionParseResult:
        """Parse een MM-beschrijving zonder bij twijfel gegevens te splitsen."""

        normalized = self._normalize_lines(value)
        lines = normalized.split("\n") if normalized else []

        colon_result = self._parse_colon_list(lines, normalized)
        if colon_result is not None:
            return colon_result

        compact_result = self._parse_compact_dot_list(lines, normalized)
        if compact_result is not None:
            return compact_result

        return self._parse_legacy_numbered_list(lines, normalized)

    def _parse_colon_list(
        self,
        lines: list[str],
        normalized: str,
    ) -> MemorixDescriptionParseResult | None:
        """Parse een aaneengesloten MM-personenlijst met ``1: Naam``."""

        first_index = next(
            (
                index
                for index, line in enumerate(lines)
                if self._colon_items_from_line(line)
            ),
            None,
        )
        if first_index is None:
            return None

        items: list[tuple[int, str]] = []
        last_index = first_index - 1
        for index in range(first_index, len(lines)):
            line = lines[index]
            line_items = self._colon_items_from_line(line)
            if line_items:
                items.extend(line_items)
                last_index = index
                continue
            if not line:
                continue
            break

        if len(items) < 2:
            return self._unreliable(
                normalized,
                "Een losse genummerde regel is onvoldoende betrouwbaar.",
            )

        names = self._validate_numbered_names(items, normalized)
        if isinstance(names, MemorixDescriptionParseResult):
            return names

        description_lines = lines[:first_index] + lines[last_index + 1 :]
        return MemorixDescriptionParseResult(
            description=self._collapse_whitespace("\n".join(description_lines)),
            names=names,
            reliable=True,
        )

    def _parse_compact_dot_list(
        self,
        lines: list[str],
        normalized: str,
    ) -> MemorixDescriptionParseResult | None:
        """Parse een compacte ``1. Naam, 2. Naam``-personenlijst."""

        for index, line in enumerate(lines):
            items = self._compact_dot_items_from_line(line)
            if len(items) < 3:
                continue
            if items[0][0] != 1:
                continue
            if not self._compact_items_look_like_names(items):
                continue

            names = self._validate_numbered_names(items, normalized)
            if isinstance(names, MemorixDescriptionParseResult):
                return names

            description_lines = lines[:index] + lines[index + 1 :]
            return MemorixDescriptionParseResult(
                description=self._collapse_whitespace("\n".join(description_lines)),
                names=names,
                reliable=True,
            )
        return None

    def _parse_legacy_numbered_list(
        self,
        lines: list[str],
        normalized: str,
    ) -> MemorixDescriptionParseResult:
        """Behoud de strenge parser voor gewone punt- en haakjeslijsten."""

        numbered_indexes = [
            index for index, line in enumerate(lines) if self._name_line.match(line)
        ]
        if not numbered_indexes:
            return self._unreliable(normalized, "Geen genummerde namenlijst gevonden.")

        first_index = numbered_indexes[0]
        header_index = first_index - 1
        has_header = header_index >= 0 and bool(
            self._header_line.match(lines[header_index])
        )
        has_blank_separator = first_index > 0 and any(
            not line for line in lines[:first_index]
        )
        if first_index == 0 or not (has_header or has_blank_separator):
            return self._unreliable(
                normalized,
                "Geen duidelijke scheiding voor namenlijst.",
            )

        trailing_lines = [line for line in lines[first_index:] if line]
        matches = [self._name_line.match(line) for line in trailing_lines]
        if not trailing_lines or any(match is None for match in matches):
            return self._unreliable(normalized, "Namenlijst bevat onherkenbare regels.")

        if len(matches) == 1 and not has_header:
            return self._unreliable(
                normalized,
                "Een losse genummerde regel is onvoldoende betrouwbaar.",
            )

        names: dict[int, str] = {}
        for expected_number, match in enumerate(matches, start=1):
            assert match is not None
            number = int(match.group(1))
            name = self._clean_name(match.group(2))
            if (
                number != expected_number
                or not self._looks_like_name(name)
                or number in names
            ):
                return self._unreliable(
                    normalized,
                    "Namenlijst is niet betrouwbaar en opeenvolgend genummerd.",
                )
            names[number] = name

        description_end = header_index if has_header else first_index
        description = "\n".join(lines[:description_end]).strip()
        return MemorixDescriptionParseResult(
            description=self._collapse_whitespace(description),
            names=names,
            reliable=True,
        )

    def _validate_numbered_names(
        self,
        items: list[tuple[int, str]],
        normalized: str,
    ) -> dict[int, str] | MemorixDescriptionParseResult:
        """Valideer een volledige reeks en sla onbekende posities over."""

        names: dict[int, str] = {}
        for expected_number, (number, raw_name) in enumerate(items, start=1):
            if number != expected_number:
                return self._unreliable(
                    normalized,
                    "Namenlijst is niet betrouwbaar en opeenvolgend genummerd.",
                )

            name = self._clean_name(raw_name)
            if not name or self._is_unknown_name(name):
                continue
            if not self._looks_like_name(name):
                return self._unreliable(
                    normalized,
                    (
                        "Namenlijst bevat een onbetrouwbare naamregel: "
                        f"{number} = {raw_name!r}"
                    ),
                )
            names[number] = name

        if not names:
            return self._unreliable(
                normalized,
                "Namenlijst bevat geen herkenbare namen.",
            )
        return names

    def _colon_items_from_line(self, line: str) -> list[tuple[int, str]]:
        """Haal één of meer ``nummer: waarde``-items uit een regel."""

        if not re.match(r"^\s*\d{1,3}:", line):
            return []
        return [
            (int(match.group(1)), match.group(2).strip())
            for match in self._colon_item.finditer(line)
        ]

    def _compact_dot_items_from_line(self, line: str) -> list[tuple[int, str]]:
        """Haal een komma-gescheiden puntlijst uit één regel."""

        stripped = line.strip()
        if not re.match(r"^1\.\s*", stripped):
            return []
        matches = list(self._compact_dot_item.finditer(stripped))
        if not matches:
            return []
        if matches[-1].end() != len(stripped):
            return []
        return [(int(match.group(1)), match.group(2).strip()) for match in matches]

    def _compact_items_look_like_names(
        self,
        items: list[tuple[int, str]],
    ) -> bool:
        """Gebruik extra strenge grenzen voor compacte puntlijsten."""

        known_names = 0
        for _, raw_name in items:
            name = self._clean_name(raw_name)
            if not name or self._is_unknown_name(name):
                continue
            if (
                not self._looks_like_name(name)
                or len(name) > 60
                or len(name.split()) > 8
                or ":" in name
            ):
                return False
            known_names += 1
        return known_names >= 2

    def _unreliable(
        self,
        description: str,
        reason: str,
    ) -> MemorixDescriptionParseResult:
        """Geef de volledige beschrijving terug wanneer splitsen onzeker is."""

        return MemorixDescriptionParseResult(
            description=self._collapse_whitespace(description),
            names={},
            reliable=False,
            reason=reason,
        )

    @staticmethod
    def _normalize_lines(value: str) -> str:
        """Normaliseer regeleinden en witruimte met behoud van lege regels."""

        raw_lines = (
            str(value or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        )
        lines = [" ".join(line.split()) for line in raw_lines]
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        return "\n".join(lines)

    @staticmethod
    def _collapse_whitespace(value: str) -> str:
        """Maak gewone beschrijving geschikt voor vergelijking en weergave."""

        return " ".join(value.split())

    @staticmethod
    def _clean_name(value: str) -> str:
        """Verwijder afsluitende leestekens uit een MM-naamregel."""

        return value.strip().rstrip(",;.").strip()

    @classmethod
    def _is_unknown_name(cls, value: str) -> bool:
        """Herken expliciet onbekende of lege persoonsposities."""

        return bool(cls._unknown_name.fullmatch(value.strip()))

    @staticmethod
    def _looks_like_name(value: str) -> bool:
        """Wijs lege, zeer lange of duidelijk beschrijvende regels af."""

        if not value or len(value) > 120:
            return False
        if value.endswith(":"):
            return False
        return any(character.isalpha() for character in value)
