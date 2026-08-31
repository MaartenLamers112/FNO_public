"""Tests voor het splitsen van MM-beschrijvingen en namenlijsten."""

from app.services.memorix_description_parser import MemorixDescriptionParser


def test_parser_splits_reliable_numbered_name_list() -> None:
    """Een duidelijk afgescheiden oplopende lijst wordt betrouwbaar gesplitst."""

    result = MemorixDescriptionParser().parse(
        "Dames na de kerk.\n\n1. Dien van Kempen,\n\n2. Truus Broeder\n\n3. Mina Jacobs"
    )

    assert result.reliable is True
    assert result.description == "Dames na de kerk."
    assert result.names == {
        1: "Dien van Kempen",
        2: "Truus Broeder",
        3: "Mina Jacobs",
    }
    assert result.reason is None


def test_parser_keeps_full_description_without_numbered_list() -> None:
    """Zonder herkenbare lijst wordt niets gesplitst."""

    result = MemorixDescriptionParser().parse("Dien, Truus en Mina voor de kerk.")

    assert result.reliable is False
    assert result.description == "Dien, Truus en Mina voor de kerk."
    assert result.names == {}


def test_parser_rejects_non_consecutive_numbering() -> None:
    """Een lijst met ontbrekende nummers is niet betrouwbaar."""

    value = "Beschrijving.\n\n1. Dien\n3. Mina"
    result = MemorixDescriptionParser().parse(value)

    assert result.reliable is False
    assert result.description == "Beschrijving. 1. Dien 3. Mina"
    assert result.names == {}


def test_parser_accepts_explicit_names_header_without_blank_line() -> None:
    """Een expliciete kop maakt de scheiding betrouwbaar."""

    result = MemorixDescriptionParser().parse(
        "Schoolklas uit 1954\nNamen:\n1. Jan Peters\n2. Marie Jansen"
    )

    assert result.reliable is True
    assert result.description == "Schoolklas uit 1954"
    assert result.names == {1: "Jan Peters", 2: "Marie Jansen"}


def test_parser_keeps_single_ambiguous_numbered_line_in_description() -> None:
    """Een losse nummerregel wordt niet als namenlijst afgesplitst."""

    source = "Beschrijving\n\n1. Eerste onderdeel van het verhaal"
    result = MemorixDescriptionParser().parse(source)

    assert result.reliable is False
    assert result.names == {}
    assert result.description == "Beschrijving 1. Eerste onderdeel van het verhaal"
