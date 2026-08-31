"""Tests voor de vergelijking met Maior Memorix."""

from app.enums.comparison_status import ComparisonStatus
from app.services.comparison_service import ComparisonService


def test_equal_metadata_is_green() -> None:
    """Gelijke betrouwbare metadata geeft groen."""

    result = ComparisonService().compare_photo_metadata(
        mm_data={
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "Schoolklas",
        },
        fno_data={
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "Schoolklas",
        },
    )

    assert result.status is ComparisonStatus.GREEN
    assert result.reliable is True
    assert all(field.equal for field in result.fields)


def test_difference_is_orange() -> None:
    """Een betrouwbaar inhoudelijk verschil geeft oranje."""

    result = ComparisonService().compare_photo_metadata(
        mm_data={"subject": "Groepsfoto"},
        fno_data={"subject": "Gewijzigde titel"},
    )

    assert result.status is ComparisonStatus.ORANGE
    assert result.fields[0].equal is False
    assert result.fields[0].mm_value == "Groepsfoto"
    assert result.fields[0].fno_value == "Gewijzigde titel"


def test_unreliable_comparison_is_red() -> None:
    """Een onbetrouwbare vergelijking is altijd rood."""

    result = ComparisonService().compare_photo_metadata(
        mm_data={"subject": "Groepsfoto"},
        fno_data={"subject": "Groepsfoto"},
        reliable=False,
    )

    assert result.status is ComparisonStatus.RED
    assert result.reliable is False


def test_comparison_ignores_non_meaningful_whitespace() -> None:
    """Niet-betekenisvolle witruimte veroorzaakt geen verschil."""

    result = ComparisonService().compare_photo_metadata(
        mm_data={"description": "Jan   en Piet\nvoor het huis"},
        fno_data={"description": " Jan en Piet voor het huis "},
    )

    description = next(field for field in result.fields if field.field == "description")
    assert description.equal is True
