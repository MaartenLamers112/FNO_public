"""Hulpfuncties voor consistente JSON-responses."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from flask import Response, jsonify
from pydantic import BaseModel


def api_response(
    schema: type[BaseModel],
    item: Any,
    *,
    status_code: int = 200,
) -> tuple[Response, int]:
    """Serialiseer één object met een Pydantic-schema."""

    data = schema.model_validate(item).model_dump(
        mode="json",
    )

    return jsonify(data), status_code


def api_list_response(
    schema: type[BaseModel],
    items: Iterable[Any],
    *,
    status_code: int = 200,
) -> tuple[Response, int]:
    """Serialiseer meerdere objecten met een Pydantic-schema."""

    data = [
        schema.model_validate(item).model_dump(
            mode="json",
        )
        for item in items
    ]

    return jsonify(data), status_code
