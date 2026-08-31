"""Hulpfuncties voor requestvalidatie in de REST API."""

from __future__ import annotations

from typing import Any

from flask import request
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.exceptions import ValidationError


def parse_json_request[SchemaT: BaseModel](schema: type[SchemaT]) -> SchemaT:
    """Valideer de JSON-body van de huidige request met een Pydantic-schema."""

    payload = request.get_json(silent=True)
    if payload is None:
        raise ValidationError(
            "De aanvraag bevat geen geldige JSON-body.",
            code="REQUEST_BODY_INVALID",
        )

    try:
        return schema.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(
            "De aanvraag bevat ongeldige velden.",
            code="REQUEST_VALIDATION_FAILED",
            details={"errors": _serialize_errors(exc)},
        ) from exc


def parse_query_request[SchemaT: BaseModel](schema: type[SchemaT]) -> SchemaT:
    """Valideer queryparameters van de huidige request met Pydantic."""

    try:
        return schema.model_validate(request.args.to_dict())
    except PydanticValidationError as exc:
        raise ValidationError(
            "De aanvraag bevat ongeldige queryparameters.",
            code="QUERY_VALIDATION_FAILED",
            details={"errors": _serialize_errors(exc)},
        ) from exc


def _serialize_errors(exc: PydanticValidationError) -> list[dict[str, Any]]:
    """Maak Pydantic-fouten veilig voor JSON-serialisatie."""

    return [
        {
            key: value
            for key, value in error.items()
            if key not in {"ctx", "input", "url"}
        }
        for error in exc.errors()
    ]
