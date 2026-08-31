"""Webtests voor het MM-vergelijkrapport en de beheerknoppen."""

from app.extensions import db
from app.models import Role, User


def create_admin() -> None:
    """Maak een beheerder voor de webtests."""

    role = Role(name="administrator", description="administrator")
    user = User(username="beheerder", role=role)
    user.set_password("test")
    db.session.add(user)
    db.session.commit()


def login(client) -> None:
    """Meld de testbeheerder aan."""

    client.post("/login", data={"username": "beheerder", "password": "test"})


def test_import_page_shows_aligned_read_only_actions(app, client, monkeypatch) -> None:
    """De MM- en parseracties staan bovenaan met de afgesproken tooltips."""

    with app.app_context():
        create_admin()
    monkeypatch.setattr(
        "app.core.routes.MmImportService.get_filter_options",
        lambda self: {},
    )
    login(client)

    response = client.get("/admin/photos/import")
    text = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "MM-gegevens aanvullen" in text
    assert "Parseranalyse downloaden" in text
    assert "MM-vergelijkrapport" in text
    assert (
        "Vult alleen lege FNO-velden vanuit MM en overschrijft nooit bestaande "
        "FNO-inhoud."
    ) in text
    assert "Read-only analyse van MM-beschrijvingen binnen de gekozen filters." in text
    assert 'form="import-filter-form"' in text


def test_administrator_can_download_mm_comparison_report(app, client, monkeypatch) -> None:
    """Beheerder kan het read-only Excel-vergelijkrapport downloaden."""

    with app.app_context():
        create_admin()
    monkeypatch.setattr(
        "app.core.routes.MmComparisonReportService.build_xlsx",
        lambda self: b"xlsx-test-data",
    )
    login(client)

    response = client.post(
        "/admin/photos/import",
        data={"action": "comparison_report"},
    )

    assert response.status_code == 200
    assert response.data == b"xlsx-test-data"
    assert response.content_type.startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "mm_vergelijkrapport_" in response.headers["Content-Disposition"]
