"""Centrale foutafhandeling voor de REST API."""

from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from app.exceptions import (
    AuthorizationError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)


def register_error_handlers(
    app: Flask,
) -> None:
    """Registreer alle API-foutafhandeling."""

    @app.errorhandler(AuthorizationError)
    def handle_authorization(error: AuthorizationError):
        status_code = 401 if error.code == "AUTHENTICATION_REQUIRED" else 403
        return (
            jsonify({
                "code": error.code,
                "message": str(error),
                "details": error.details,
            }),
            status_code,
        )

    @app.errorhandler(NotFoundError)
    def handle_not_found(error: NotFoundError):
        return (
            jsonify({
                "code": error.code,
                "message": str(error),
                "details": error.details,
            }),
            404,
        )

    @app.errorhandler(ValidationError)
    def handle_validation(error: ValidationError):
        return (
            jsonify({
                "code": error.code,
                "message": str(error),
                "details": error.details,
            }),
            400,
        )

    @app.errorhandler(ConflictError)
    def handle_conflict(error: ConflictError):
        return (
            jsonify({
                "code": error.code,
                "message": str(error),
                "details": error.details,
            }),
            409,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(error: RequestEntityTooLarge):
        del error
        return (
            jsonify({
                "code": "REQUEST_TOO_LARGE",
                "message": "Het aangeleverde bestand is te groot.",
                "details": {},
            }),
            413,
        )

    @app.errorhandler(ExternalServiceError)
    def handle_external_service(error: ExternalServiceError):
        return (
            jsonify({
                "code": error.code,
                "message": str(error),
                "details": error.details,
            }),
            502,
        )
