"""Tests voor bulkimport uit Maior Memorix."""

from app.extensions import db
from app.models import Photo, Role, User
from app.repositories import PhotoRepository


def create_user(*, role_name: str, username: str) -> None:
    """Maak een testgebruiker met rol."""

    role = Role(name=role_name, description=role_name)
    user = User(username=username, role=role)
    user.set_password("test")
    db.session.add(user)
    db.session.commit()


def login(client, username: str) -> None:
    """Meld een testgebruiker aan."""

    client.post("/login", data={"username": username, "password": "test"})


def sample_record() -> dict[str, object]:
    """Geef een representatief MM-zoekresultaat."""

    return {
        "fields": {
            "delving_hubId": ["MM-NEW-001"],
            "dc_identifier": ["A19011"],
            "dc_title": ["Priesterwijding P. Stevens"],
            "dc_subject": ["Personen", "Religie"],
            "dcterms_created": ["1939"],
            "tib_place": ["Vortum-Mullem"],
            "tib_collectionPart": ["Vortum-Mullem"],
            "delving_thumbnail": ["https://example.test/thumb.jpg"],
        }
    }


def test_import_page_requires_administrator(app, client) -> None:
    """Een medewerker mag de MM-import niet openen."""

    with app.app_context():
        create_user(role_name="employee", username="medewerker")
    login(client, "medewerker")
    assert client.get("/admin/photos/import").status_code == 403


def test_administrator_can_open_import_page(app, client) -> None:
    """Een beheerder kan de importpagina openen."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")
    login(client, "beheerder")
    response = client.get("/admin/photos/import")
    assert response.status_code == 200
    assert b"Deelcollectie" in response.data
    assert b"Voorvertoning ophalen" in response.data


def test_administrator_can_preview_collection_part(app, client, monkeypatch) -> None:
    """Een harde deelcollectiefilter levert een voorvertoning."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.search_records_page",
        lambda self, filters, page, page_size: ([sample_record()], 1),
    )
    login(client, "beheerder")
    response = client.post(
        "/admin/photos/import",
        data={"action": "preview", "collection_part": "Vortum-Mullem"},
    )
    assert response.status_code == 200
    assert b"A19011" in response.data
    assert b"Importeer <span data-import-count>0</span> foto's" in response.data
    assert b"https://example.test/thumb.jpg" in response.data
    assert b"Personen; Religie" in response.data
    assert b'data-status="new"' in response.data


def test_administrator_can_bulk_import(app, client, monkeypatch) -> None:
    """Nieuwe MM-records worden als concept met metadata opgeslagen."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.search_records_page",
        lambda self, filters, page, page_size: ([sample_record()], 1),
    )
    login(client, "beheerder")
    response = client.post(
        "/admin/photos/import",
        data={
            "action": "import",
            "collection_part": "Vortum-Mullem",
            "selected_mm_ids": "MM-NEW-001",
        },
    )
    assert response.status_code == 200
    with app.app_context():
        photo = PhotoRepository().get_by_mm_id("MM-NEW-001")
        assert photo is not None
        assert photo.photo_number == "A19011"
        assert photo.publication_status == 0
        assert photo.mm_metadata["tib_collectionPart"] == ["Vortum-Mullem"]


def test_import_preview_contains_selection_controls(app, client, monkeypatch) -> None:
    """De voorvertoning ondersteunt filteren en handmatige selectie."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.search_records_page",
        lambda self, filters, page, page_size: ([sample_record()], 1),
    )
    login(client, "beheerder")

    response = client.post(
        "/admin/photos/import",
        data={"action": "preview", "collection_part": "Vortum-Mullem"},
    )

    assert response.status_code == 200
    assert b'data-column-filter="status"' in response.data
    assert b'data-column-filter="photo-number"' in response.data
    assert b"data-select-visible" in response.data
    assert b'name="selected_mm_ids"' in response.data
    assert b"admin/import-preview.js" in response.data


def test_import_preview_is_paginated(app, client, monkeypatch) -> None:
    """De MM-voorvertoning haalt slechts één pagina tegelijk op."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")

    calls: list[tuple[int, int]] = []

    def fake_search_page(self, filters, page, page_size):
        calls.append((page, page_size))
        return [sample_record()], 250

    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.search_records_page",
        fake_search_page,
    )
    login(client, "beheerder")

    response = client.post(
        "/admin/photos/import",
        data={
            "collection_part": "Vortum-Mullem",
            "page": "1",
            "page_target": "2",
        },
    )

    assert response.status_code == 200
    assert calls == [(2, 100)]
    assert b"250</strong> gevonden" in response.data
    assert b"Pagina 2 van 3" in response.data
    assert b"Vorige 100" in response.data
    assert b"Volgende 100" in response.data


def test_administrator_can_supplement_empty_mm_metadata(
    app, client, monkeypatch
) -> None:
    """Een beheerder kan lege FNO-metadata expliciet vanuit MM aanvullen."""

    with app.app_context():
        create_user(role_name="administrator", username="beheerder")
        repository = PhotoRepository()
        repository.add(
            Photo(
                mm_id="MM-NEW-001",
                photo_number="A19011",
                publication_status=0,
                local_subject="Eigen onderwerp",
            )
        )
        repository.save()

    def fake_get_metadata_record(self, mm_id: str):
        assert mm_id == "MM-NEW-001"
        fields = sample_record()["fields"]
        return fields, self.normalize_metadata_from_fields(fields)

    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_metadata_record",
        fake_get_metadata_record,
    )
    login(client, "beheerder")

    response = client.post(
        "/admin/photos/import",
        data={"action": "supplement"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"MM-gegevens aanvullen" in response.data
    assert b"lege velden" in response.data
    with app.app_context():
        photo = PhotoRepository().get_by_mm_id("MM-NEW-001")
        assert photo is not None
        assert photo.local_subject == "Eigen onderwerp"
        assert photo.local_date == "1939"
        assert photo.local_location == "Vortum-Mullem"
