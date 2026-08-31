"""Regressievoorbeelden voor toekomstige MM-parserverbetering.

De voorbeelden komen uit de read-only analyse van de deelcollectie Vortum-Mullem.
Negatieve gevallen leggen het veiligheidsniveau vast.
Positieve gevallen leggen ondersteunde echte MM-personenlijsten vast.
"""

import pytest

from app.services.memorix_description_parser import MemorixDescriptionParser

parser = MemorixDescriptionParser()


@pytest.mark.parametrize(
    ("description", "expected_description", "expected_names"),
    [
        (
            """Vortum-Mullem: Feestelijke gebeurtenis in Vortum-Mullem
1: Jan Broeder
2: Wim Gerrits
3: Toon Leenders
4: Jan Ronnes""",
            "Vortum-Mullem: Feestelijke gebeurtenis in Vortum-Mullem",
            {
                1: "Jan Broeder",
                2: "Wim Gerrits",
                3: "Toon Leenders",
                4: "Jan Ronnes",
            },
        ),
        (
            """Derde klas. Deze kinderen verlieten de lagere school in 1973

1: Karin van Bree
2: Wilma Jacobs
3: Angelique Martens
4: Marian Leenders""",
            "Derde klas. Deze kinderen verlieten de lagere school in 1973",
            {
                1: "Karin van Bree",
                2: "Wilma Jacobs",
                3: "Angelique Martens",
                4: "Marian Leenders",
            },
        ),
        (
            """Het ongeorganiseerd voetballen na de school liep op rolletjes.

1: Herman Keijzers
2: Martien Fransen
3: Toon Gerrits
4: Wim van de Krabben""",
            "Het ongeorganiseerd voetballen na de school liep op rolletjes.",
            {
                1: "Herman Keijzers",
                2: "Martien Fransen",
                3: "Toon Gerrits",
                4: "Wim van de Krabben",
            },
        ),
        (
            """Vortum-Mullem:
1: William Jacobs
2: Monique van de Poel
3: Jacqueline van de Poel
4: Inge Rutten

Zie ook A10616, A10619 en A10620.""",
            "Vortum-Mullem: Zie ook A10616, A10619 en A10620.",
            {
                1: "William Jacobs",
                2: "Monique van de Poel",
                3: "Jacqueline van de Poel",
                4: "Inge Rutten",
            },
        ),
        (
            """Vortum-Mullem: Bestuur 60 jaar NCB Vortum-Mullem
1: Hendrik Deenen
2: Thyke Jacobs
3: Koos van Bree
4: Bert Ebben""",
            "Vortum-Mullem: Bestuur 60 jaar NCB Vortum-Mullem",
            {
                1: "Hendrik Deenen",
                2: "Thyke Jacobs",
                3: "Koos van Bree",
                4: "Bert Ebben",
            },
        ),
        (
            """Vortum-Mullem: Inzegening school
1:
2: Thij van Bree
3: Pastoor P. Vossen
4: Piet Wientjes
5:
6: Jo Thissen
7: Willebrord Ronnes""",
            "Vortum-Mullem: Inzegening school",
            {
                2: "Thij van Bree",
                3: "Pastoor P. Vossen",
                4: "Piet Wientjes",
                6: "Jo Thissen",
                7: "Willebrord Ronnes",
            },
        ),
    ],
)
def test_parser_accepts_real_numbered_person_lists(
    description: str,
    expected_description: str,
    expected_names: dict[int, str],
) -> None:
    """Leg gewenste betrouwbare personenlijsten uit echte MM-data vast."""

    result = parser.parse(description)

    assert result.reliable is True
    assert result.description == expected_description
    assert result.names == expected_names


@pytest.mark.parametrize(
    "description",
    [
        (
            "Kar en paard zou van Verberkt zijn. "
            "De luchtbescherming verspreidde een lijst met tips voor zelfbescherming:\n"
            "1. Een verbanddoos met watten en veiligheidsspelden.\n"
            "2. Voor brandblussen twee emmers water en droog zand.\n"
            "3. Een metalen hoofddeksel ter voorkoming van hoofdkwetsuren."
        ),
        (
            "De familie Thissen in 1925. Christiaan trouwt "
            "1) met Mieke Steenbergen en 2) met Drika Fleuren."
        ),
        (
            "In het overlijdensboek staat dat Oswaldus Vink weduwnaar was van "
            "1. Huberdina Helena Hanckx en 2. Anna Gertrudis Zeegers."
        ),
        (
            "De gemeentelijke vergoedingen beliepen een periode van 5 jaar. "
            "Het overschot werd gebruikt voor een filmprojector. "
            "Hier kijken Frans Verberkt, Jan Jans en Wim Derks van de Ven."
        ),
    ],
)
def test_parser_keeps_non_person_numbering_untouched(description: str) -> None:
    """Niet-persoonsnummering mag nooit als namenlijst worden afgesplitst."""

    result = parser.parse(description)

    assert result.reliable is False
    assert result.names == {}
    assert result.description == " ".join(description.split())


def test_existing_supported_names_header_remains_reliable() -> None:
    """Het reeds ondersteunde expliciete Namen-patroon blijft geldig."""

    description = """Groepsfoto.

Namen:
1. Jan Jansen
2. Piet Peters"""

    result = parser.parse(description)

    assert result.reliable is True
    assert result.description == "Groepsfoto."
    assert result.names == {1: "Jan Jansen", 2: "Piet Peters"}


def test_parser_skips_question_mark_unknown_positions() -> None:
    """Vraagtekens behouden de positie maar maken geen persoon aan."""

    description = """Vortum-Mullem: Optocht
1: Grada Gerrits
2: Drika van Kempen
3: Coba van Bree
4: Hanna Gerrits
5: Lies Gerrits
6: ?
7: ?"""

    result = parser.parse(description)

    assert result.reliable is True
    assert result.description == "Vortum-Mullem: Optocht"
    assert result.names == {
        1: "Grada Gerrits",
        2: "Drika van Kempen",
        3: "Coba van Bree",
        4: "Hanna Gerrits",
        5: "Lies Gerrits",
    }


def test_parser_accepts_two_colon_items_on_one_physical_line() -> None:
    """Accepteer twee dubbelepunt-items op één fysieke regel."""

    description = """Vortum-Mullem: Vormelingen
1:
2: William Jacobs
3: Monique van de Poel
4: Jacqueline van de Poel
5: Inge Rutten
6: Lieveke van Uden
7: Monseigneur Bluyssen
8: Maarten Ebben
9: Peter van Raaij
10: Jan Brienen
11: Geert Jan van Uden
12: Erik Ronnes
13: Martien Weijers
14: Jolanda Hermans
15: Yvonne Jakobs (PD)
16: Yvonne Jakobs (GD)
17: Mark Ronnes 18: Mark Creemers
19: Christa Toonen

Zie ook A10618, A10619 en A10620."""

    result = parser.parse(description)

    assert result.reliable is True
    assert result.names[17] == "Mark Ronnes"
    assert result.names[18] == "Mark Creemers"
    assert result.names[19] == "Christa Toonen"
    assert 1 not in result.names
    assert result.description == (
        "Vortum-Mullem: Vormelingen Zie ook A10618, A10619 en A10620."
    )


def test_parser_accepts_compact_dot_person_list_with_unknowns() -> None:
    """Een compacte volledige puntlijst met korte naamitems wordt herkend."""

    description = (
        "Uitstapje van de Landbouwschool naar de Rosmolen in Geysteren.\n"
        "1. Gerrit Rutten, 2. ......., 3. ......, 4. ......., "
        "5. Marthien Crooijmans, 6. Nico Vloet, 7. Jan Pennings, "
        "8. ........, 9. Piet v.d. Zanden, 10. ......., "
        "11. Bert van Mil, 12. Loed van Dijk, 13. ......., "
        "14. Piet van Keijsteren"
    )

    result = parser.parse(description)

    assert result.reliable is True
    assert result.description == (
        "Uitstapje van de Landbouwschool naar de Rosmolen in Geysteren."
    )
    assert result.names == {
        1: "Gerrit Rutten",
        5: "Marthien Crooijmans",
        6: "Nico Vloet",
        7: "Jan Pennings",
        9: "Piet v.d. Zanden",
        11: "Bert van Mil",
        12: "Loed van Dijk",
        14: "Piet van Keijsteren",
    }


def test_compact_dot_list_requires_at_least_three_sequential_items() -> None:
    """Huwelijksnummering met twee items blijft gewone beschrijving."""

    description = (
        "Oswaldus Vink was weduwnaar van 1. Huberdina Helena Hanckx en "
        "2. Anna Gertrudis Zeegers."
    )

    result = parser.parse(description)

    assert result.reliable is False
    assert result.names == {}
    assert result.description == description
