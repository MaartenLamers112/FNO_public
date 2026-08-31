"""Bedrijfslogica voor vergelijking met Maior Memorix."""

from collections.abc import Iterable, Mapping
from typing import Any

from app.enums.comparison_status import ComparisonStatus
from app.schemas.comparison_schema import (
    FieldComparisonResponse,
    PersonComparisonResponse,
    PhotoComparisonResponse,
)


class ComparisonService:
    """Vergelijk FNO-gegevens met live MM-gegevens."""

    FIELD_NAMES = ("subject", "date", "location", "description")

    def compare_photo(
        self,
        *,
        mm_data: Mapping[str, object],
        fno_data: Mapping[str, object],
        mm_names: Mapping[int, str],
        fno_persons: Iterable[Any],
        names_reliable: bool,
        reason: str | None = None,
    ) -> PhotoComparisonResponse:
        """Vergelijk metadata en persoonsnamen en bepaal de totaalstatus."""

        fields = [
            self._compare_field(
                field=field,
                mm_value=mm_data.get(field),
                fno_value=fno_data.get(field),
                reliable=field != "description" or names_reliable,
            )
            for field in self.FIELD_NAMES
        ]
        persons = self._compare_persons(
            mm_names=mm_names,
            fno_persons=fno_persons,
            reliable=names_reliable,
        )
        statuses = [item.status for item in [*fields, *persons]]

        return PhotoComparisonResponse(
            status=self._aggregate_status(statuses),
            reliable=names_reliable,
            reason=reason,
            fields=fields,
            persons=persons,
        )

    def compare_photo_metadata(
        self,
        *,
        mm_data: Mapping[str, object],
        fno_data: Mapping[str, object],
        reliable: bool = True,
    ) -> PhotoComparisonResponse:
        """Vergelijk alleen metadata voor gerichte toepassingen en tests."""

        fields = [
            self._compare_field(
                field=field,
                mm_value=mm_data.get(field),
                fno_value=fno_data.get(field),
                reliable=reliable,
            )
            for field in self.FIELD_NAMES
        ]
        return PhotoComparisonResponse(
            status=self._aggregate_status([field.status for field in fields]),
            reliable=reliable,
            fields=fields,
        )

    def _compare_persons(
        self,
        *,
        mm_names: Mapping[int, str],
        fno_persons: Iterable[Any],
        reliable: bool,
    ) -> list[PersonComparisonResponse]:
        """Vergelijk namen op basis van het labelnummer."""

        fno_names = {
            int(person.label_number): self._normalize_value(person.current_name)
            for person in fno_persons
        }
        comparisons = []
        for label_number in sorted(set(mm_names) | set(fno_names)):
            mm_name = self._normalize_value(mm_names.get(label_number))
            fno_name = fno_names.get(label_number, "")
            equal = reliable and mm_name == fno_name
            comparisons.append(
                PersonComparisonResponse(
                    label_number=label_number,
                    mm_name=mm_name,
                    fno_name=fno_name,
                    equal=equal,
                    status=self._status(equal=equal, reliable=reliable),
                )
            )
        return comparisons

    def _compare_field(
        self,
        *,
        field: str,
        mm_value: object,
        fno_value: object,
        reliable: bool,
    ) -> FieldComparisonResponse:
        """Vergelijk één metadata-veld na minimale normalisatie."""

        normalized_mm = self._normalize_value(mm_value)
        normalized_fno = self._normalize_value(fno_value)
        equal = reliable and normalized_mm == normalized_fno
        return FieldComparisonResponse(
            field=field,
            mm_value=normalized_mm,
            fno_value=normalized_fno,
            equal=equal,
            status=self._status(equal=equal, reliable=reliable),
        )

    @staticmethod
    def _status(*, equal: bool, reliable: bool) -> ComparisonStatus:
        """Bepaal de kleurstatus van één vergelijking."""

        if not reliable:
            return ComparisonStatus.RED
        return ComparisonStatus.GREEN if equal else ComparisonStatus.ORANGE

    @staticmethod
    def _aggregate_status(statuses: list[ComparisonStatus]) -> ComparisonStatus:
        """Laat rood voorgaan op oranje en oranje op groen."""

        if ComparisonStatus.RED in statuses:
            return ComparisonStatus.RED
        if ComparisonStatus.ORANGE in statuses:
            return ComparisonStatus.ORANGE
        return ComparisonStatus.GREEN

    @staticmethod
    def _normalize_value(value: object) -> str:
        """Normaliseer lege waarden en niet-betekenisvolle witruimte."""

        if value is None:
            return ""
        return " ".join(str(value).split())
