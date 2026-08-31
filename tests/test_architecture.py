"""Architectuurcontroles voor de afgesproken FNO-lagen."""

from __future__ import annotations

import ast
from pathlib import Path

APP_ROOT = Path(__file__).parents[1] / "app"


def test_database_session_is_only_used_by_repositories() -> None:
    """Applicatielagen buiten repositories gebruiken geen SQLAlchemy-sessie."""

    violations: list[str] = []
    for path in APP_ROOT.rglob("*.py"):
        if "repositories" in path.parts or path.name == "extensions.py":
            continue
        source = path.read_text(encoding="utf-8")
        if "db.session" in source:
            violations.append(str(path.relative_to(APP_ROOT.parent)))

    assert violations == []


def test_api_does_not_call_private_service_methods() -> None:
    """API-routes gebruiken uitsluitend de publieke service-interface."""

    violations: list[str] = []
    for path in (APP_ROOT / "api").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr.startswith("_") and not node.func.attr.startswith("__"):
                violations.append(
                    f"{path.relative_to(APP_ROOT.parent)}:{node.lineno}:{node.func.attr}"
                )

    assert violations == []


def test_wsgi_entrypoint_uses_production_configuration() -> None:
    """Het WSGI-entrypoint start altijd met de productieconfiguratie."""

    project_root = APP_ROOT.parent
    source = (project_root / "wsgi.py").read_text(encoding="utf-8")

    assert 'create_app("production")' in source


def test_env_example_keeps_default_sqlite_location() -> None:
    """De voorbeeldconfiguratie overschrijft het vaste SQLite-pad niet."""

    project_root = APP_ROOT.parent
    source = (project_root / ".env.example").read_text(encoding="utf-8")

    assert "DATABASE_URL=sqlite:///fno.db" not in source
