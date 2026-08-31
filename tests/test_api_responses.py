"""Tests voor algemene API-responsehelpers."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from app.api.responses import api_list_response, api_response


class ExampleResponse(BaseModel):
    """Eenvoudig schema voor response-tests."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


@dataclass(slots=True)
class ExampleObject:
    """Eenvoudig object dat via attributen wordt geserialiseerd."""

    id: int
    name: str


def test_api_response_serializes_dictionary(app) -> None:
    """Een dictionary wordt als JSON-object teruggegeven."""

    item = {
        "id": 1,
        "name": "Voorbeeld",
    }

    with app.app_context():
        response, status_code = api_response(
            ExampleResponse,
            item,
        )

    assert status_code == 200
    assert response.get_json() == {
        "id": 1,
        "name": "Voorbeeld",
    }


def test_api_response_serializes_object_attributes(app) -> None:
    """Een object kan via zijn attributen worden geserialiseerd."""

    item = ExampleObject(
        id=2,
        name="Object",
    )

    with app.app_context():
        response, status_code = api_response(
            ExampleResponse,
            item,
        )

    assert status_code == 200
    assert response.get_json() == {
        "id": 2,
        "name": "Object",
    }


def test_api_list_response_serializes_multiple_items(app) -> None:
    """Meerdere objecten worden als JSON-lijst teruggegeven."""

    items = [
        ExampleObject(
            id=1,
            name="Eerste",
        ),
        ExampleObject(
            id=2,
            name="Tweede",
        ),
    ]

    with app.app_context():
        response, status_code = api_list_response(
            ExampleResponse,
            items,
        )

    assert status_code == 200
    assert response.get_json() == [
        {
            "id": 1,
            "name": "Eerste",
        },
        {
            "id": 2,
            "name": "Tweede",
        },
    ]


def test_api_list_response_supports_empty_collection(app) -> None:
    """Een lege verzameling wordt een lege JSON-lijst."""

    with app.app_context():
        response, status_code = api_list_response(
            ExampleResponse,
            [],
        )

    assert status_code == 200
    assert response.get_json() == []


def test_api_response_supports_custom_status_code(app) -> None:
    """Een afwijkende HTTP-status kan worden ingesteld."""

    item = {
        "id": 1,
        "name": "Aangemaakt",
    }

    with app.app_context():
        response, status_code = api_response(
            ExampleResponse,
            item,
            status_code=201,
        )

    assert status_code == 201
    assert response.get_json() == {
        "id": 1,
        "name": "Aangemaakt",
    }


def test_api_list_response_supports_custom_status_code(app) -> None:
    """Ook een lijstresponse ondersteunt een afwijkende status."""

    items = [
        {
            "id": 1,
            "name": "Voorbeeld",
        },
    ]

    with app.app_context():
        response, status_code = api_list_response(
            ExampleResponse,
            items,
            status_code=202,
        )

    assert status_code == 202
    assert response.get_json() == [
        {
            "id": 1,
            "name": "Voorbeeld",
        },
    ]
