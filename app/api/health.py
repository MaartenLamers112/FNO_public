"""Healthcheck-endpoint voor Foto Nummeraar Online."""

from flask import Blueprint, jsonify

health_blueprint = Blueprint(
    "health",
    __name__,
)


@health_blueprint.get("/health")
def health_check():
    """Controleer of de applicatie bereikbaar is."""

    return jsonify({
        "status": "ok",
        "application": "Foto Nummeraar Online",
    })
