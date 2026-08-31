"""Tests voor de REST API voor foto's."""

from io import BytesIO

from app.enums.author_type import AuthorType
from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import (
    CommentRepository,
    PersonRepository,
    PhotoRepository,
)


def test_get_photos_returns_empty_collection(client) -> None:
    """Zonder foto's geeft de endpoint een lege collectie terug."""

    response = client.get("/api/photos")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [],
        "locations": [],
    }


def test_get_photos_returns_landing_data(client, app, monkeypatch) -> None:
    """De endpoint combineert lokale foto's met live MM-lijstgegevens."""

    repository = PhotoRepository()

    repository.add(
        Photo(
            mm_id="MM-API-001",
            photo_number="A90001",
            publication_status=PublicationStatus.CONCEPT,
            is_visible=True,
            local_subject="Schoolklas",
            local_date="1954",
            local_location="Vortum-Mullem",
        )
    )
    repository.add(
        Photo(
            mm_id="MM-API-002",
            photo_number="A90002",
            publication_status=PublicationStatus.PUBLISHED,
            is_visible=True,
            local_subject="Voetbalelftal",
            local_date="1962",
            local_location="Boxmeer",
        )
    )
    repository.save()

    def fake_get_landing_data(self, mm_id: str) -> dict[str, str]:
        return {
            "thumbnail_url": f"https://images.example.test/{mm_id}.jpg",
            "subject": "Schoolklas" if mm_id.endswith("001") else "Voetbalelftal",
            "date": "1954" if mm_id.endswith("001") else "1962",
            "location": "Vortum-Mullem",
        }

    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_landing_data",
        fake_get_landing_data,
    )

    response = client.get("/api/photos")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [
            {
                "id": 1,
                "mm_id": "MM-API-001",
                "photo_number": "A90001",
                "publication_status": "concept",
                "progress_status": "partial",
                "is_visible": True,
                "is_complete": False,
                "thumbnail_url": "https://images.example.test/MM-API-001.jpg",
                "subject": "Schoolklas",
                "date": "1954",
                "location": "Vortum-Mullem",
            },
            {
                "id": 2,
                "mm_id": "MM-API-002",
                "photo_number": "A90002",
                "publication_status": "published",
                "progress_status": "partial",
                "is_visible": True,
                "is_complete": False,
                "thumbnail_url": "https://images.example.test/MM-API-002.jpg",
                "subject": "Voetbalelftal",
                "date": "1962",
                "location": "Boxmeer",
            },
        ],
        "locations": ["Boxmeer", "Vortum-Mullem"],
    }


def test_get_photos_applies_search_status_and_location_filters(
    client,
    app,
    monkeypatch,
) -> None:
    """Zoeken en filters worden in de servicelaag toegepast."""

    repository = PhotoRepository()
    repository.add(
        Photo(
            mm_id="MM-FILTER-001",
            photo_number="A91001",
            publication_status=PublicationStatus.CONCEPT,
            is_visible=True,
            local_subject="Schoolklas",
            local_date="1954",
            local_location="Vortum-Mullem",
        )
    )
    repository.add(
        Photo(
            mm_id="MM-FILTER-002",
            photo_number="A91002",
            publication_status=PublicationStatus.PUBLISHED,
            is_visible=True,
            local_subject="Voetbalelftal",
            local_date="1962",
            local_location="Boxmeer",
        )
    )
    repository.save()

    data = {
        "MM-FILTER-001": {
            "thumbnail_url": "https://images.example.test/1.jpg",
            "subject": "Schoolklas",
            "date": "1954",
            "location": "Vortum-Mullem",
        },
        "MM-FILTER-002": {
            "thumbnail_url": "https://images.example.test/2.jpg",
            "subject": "Voetbalelftal",
            "date": "1962",
            "location": "Boxmeer",
        },
    }
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_landing_data",
        lambda self, mm_id: data[mm_id],
    )

    response = client.get("/api/photos?search=voetbal&status=partial&location=Boxmeer")

    assert response.status_code == 200
    payload = response.get_json()
    assert [item["photo_number"] for item in payload["items"]] == ["A91002"]
    assert payload["locations"] == ["Boxmeer", "Vortum-Mullem"]


def test_get_photos_rejects_invalid_query(client) -> None:
    """Ongeldige filterwaarden geven een validatiefout."""

    response = client.get("/api/photos?status=invalid&sort=unknown")

    assert response.status_code == 400


def test_get_existing_photo(client, app, monkeypatch) -> None:
    """Een bestaande foto kan worden opgehaald."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM-API-101",
            photo_number="A90101",
            publication_status=PublicationStatus.CONCEPT,
            is_visible=True,
        )
    )
    repository.save()

    def fake_get_photo_data(self, mm_id: str) -> dict[str, str]:
        assert mm_id == "MM-API-101"
        return {
            "image_source": "https://images.example.test/photo.dzi",
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
        }

    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        fake_get_photo_data,
    )

    response = client.get(f"/api/photos/{photo.id}")

    assert response.status_code == 200

    assert response.get_json() == {
        "id": photo.id,
        "mm_id": "MM-API-101",
        "photo_number": "A90101",
        "person_display_mode": "numbered",
        "person_display_count": 1,
        "label_size": 14,
        "publication_status": "concept",
        "progress_status": "empty",
        "is_visible": True,
        "is_complete": False,
        "previous_photo_id": None,
        "next_photo_id": None,
        "image_source": "https://images.example.test/photo.dzi",
        "subject": "",
        "date": "",
        "location": "",
        "description": "",
    }


def test_employee_gets_photo_comparison(
    client, app, authenticated_employee, monkeypatch
) -> None:
    """Medewerkers ontvangen de automatische MM-vergelijking."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-COMPARE-API-001",
            photo_number="A90102",
            publication_status=PublicationStatus.CONCEPT,
            local_subject="Aangepast onderwerp",
        )
    )
    repository.save()

    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://images.example.test/photo.dzi",
            "subject": "MM-onderwerp",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "",
        },
    )

    response = client.get(f"/api/photos/{photo.id}")

    assert response.status_code == 200
    comparison = response.get_json()["comparison"]
    assert comparison["status"] == "red"
    assert comparison["fields"][0] == {
        "field": "subject",
        "mm_value": "MM-onderwerp",
        "fno_value": "Aangepast onderwerp",
        "equal": False,
        "status": "orange",
    }


def test_visitor_does_not_receive_comparison(client, app, monkeypatch) -> None:
    """Bezoekers ontvangen geen interne MM-vergelijkgegevens."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-COMPARE-PUBLIC-001",
            photo_number="A90103",
            publication_status=PublicationStatus.PUBLISHED,
            is_visible=True,
        )
    )
    repository.save()
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://images.example.test/photo.dzi",
            "subject": "Onderwerp",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "",
        },
    )

    payload = client.get(f"/api/photos/{photo.id}").get_json()

    assert "comparison" not in payload


def test_get_unknown_photo_returns_404(client) -> None:
    """Een onbekende foto geeft HTTP 404."""

    response = client.get("/api/photos/999999")

    assert response.status_code == 404


def test_get_photo_persons_returns_empty_list(client, app) -> None:
    """Een foto zonder labels geeft een lege lijst terug."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM-API-PERSONS-001",
            photo_number="A90201",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.get(f"/api/photos/{photo.id}/persons")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_photo_persons_returns_ordered_labels(client, app) -> None:
    """Labels worden op labelnummer teruggegeven."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()

    photo = photo_repository.add(
        Photo(
            mm_id="MM-API-PERSONS-002",
            photo_number="A90202",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    photo_repository.save()

    second = person_repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.40,
        y_position=0.50,
        current_name="Piet Jansen",
    )

    first = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.20,
        y_position=0.30,
        current_name="Jan Peters",
    )

    person_repository.save()

    response = client.get(f"/api/photos/{photo.id}/persons")

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "id": first.id,
            "photo_id": photo.id,
            "label_number": 1,
            "x_position": 0.20,
            "y_position": 0.30,
            "current_name": "Jan Peters",
            "name_locked": False,
        },
        {
            "id": second.id,
            "photo_id": photo.id,
            "label_number": 2,
            "x_position": 0.40,
            "y_position": 0.50,
            "current_name": "Piet Jansen",
            "name_locked": False,
        },
    ]


def test_get_persons_for_unknown_photo_returns_404(client) -> None:
    """Labels van een onbekende foto geven HTTP 404."""

    response = client.get("/api/photos/999999/persons")

    assert response.status_code == 404
    assert response.get_json() == {
        "code": "PHOTO_NOT_FOUND",
        "message": "De foto bestaat niet.",
        "details": {
            "photo_id": 999999,
        },
    }


def test_get_photo_comments_returns_empty_list(
    client,
    app,
) -> None:
    """Een foto zonder opmerkingen geeft een lege lijst terug."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id="MM-API-COMMENT-001",
            photo_number="A90301",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    repository.save()

    response = client.get(f"/api/photos/{photo.id}/comments")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_photo_comments_returns_comments(
    client,
    app,
) -> None:
    """Opmerkingen worden teruggegeven."""

    photo_repository = PhotoRepository()
    comment_repository = CommentRepository()

    photo = photo_repository.add(
        Photo(
            mm_id="MM-API-COMMENT-002",
            photo_number="A90302",
            publication_status=PublicationStatus.CONCEPT,
        )
    )

    photo_repository.save()

    first = comment_repository.create(
        photo_id=photo.id,
        content="Eerste opmerking",
        author_type=AuthorType.VISITOR,
    )

    second = comment_repository.create(
        photo_id=photo.id,
        content="Tweede opmerking",
        author_type=AuthorType.EMPLOYEE,
    )

    comment_repository.save()

    response = client.get(f"/api/photos/{photo.id}/comments")

    assert response.status_code == 200

    assert response.get_json() == [
        {
            "id": first.id,
            "photo_id": photo.id,
            "person_id": None,
            "content": "Eerste opmerking",
            "author_type": "visitor",
            "status": "open",
            "created_at": first.created_at.isoformat(),
        },
        {
            "id": second.id,
            "photo_id": photo.id,
            "person_id": None,
            "content": "Tweede opmerking",
            "author_type": "employee",
            "status": "open",
            "created_at": second.created_at.isoformat(),
        },
    ]


def test_get_comments_unknown_photo_returns_404(
    client,
) -> None:
    """Een onbekende foto geeft HTTP 404."""

    response = client.get("/api/photos/999999/comments")

    assert response.status_code == 404

    assert response.get_json() == {
        "code": "PHOTO_NOT_FOUND",
        "message": "De foto bestaat niet.",
        "details": {
            "photo_id": 999999,
        },
    }


def test_admin_can_change_photo_publication_status(
    client, app, authenticated_admin
) -> None:
    """Een beheerder kan de publicatiestatus wijzigen."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-PUBLICATION-001",
            photo_number="A99001",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.patch(
        f"/api/photos/{photo.id}/publication-status",
        json={"publication_status": "published"},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 200
    assert response.get_json()["publication_status"] == "published"


def test_employee_cannot_change_photo_publication_status(
    client, app, authenticated_employee
) -> None:
    """Een medewerker kan de publicatiestatus niet wijzigen."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-PUBLICATION-002",
            photo_number="A99002",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.patch(
        f"/api/photos/{photo.id}/publication-status",
        json={"publication_status": "published"},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 403


def test_employee_can_auto_label_photo(
    client,
    authenticated_employee,
    monkeypatch,
) -> None:
    """Een medewerker kan echte labels automatisch laten aanmaken."""

    from app.models import Person
    from app.services import AutoLabelResult, PersonDetectionService

    monkeypatch.setattr(
        PersonDetectionService,
        "auto_label",
        lambda self, **kwargs: AutoLabelResult(
            persons=[
                Person(
                    id=1,
                    photo_id=1,
                    label_number=1,
                    x_position=0.25,
                    y_position=0.30,
                    name_locked=False,
                )
            ],
            detected_count=1,
            created_count=1,
            skipped_existing_count=0,
            model_name="test-model",
            source_width=220,
            source_height=160,
            analysis_width=220,
            analysis_height=160,
            detection_passes=1,
            image_load_duration_ms=1,
            detector_load_duration_ms=0,
            inference_duration_ms=10,
            duration_ms=11,
        ),
    )

    response = client.post(
        "/api/photos/1/auto-label",
        data={"image": (BytesIO(b"image"), "photo.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.get_json()["created_count"] == 1
    assert response.get_json()["persons"][0]["label_number"] == 1


def test_visitor_cannot_auto_label_photo(client) -> None:
    """Een bezoeker kan geen automatische labels aanmaken."""

    response = client.post(
        "/api/photos/1/auto-label",
        data={"image": (BytesIO(b"image"), "photo.jpg")},
        content_type="multipart/form-data",
    )

    assert response.status_code in {302, 401, 403}


def test_employee_can_export_photo_json(
    client,
    app,
    authenticated_employee,
    monkeypatch,
) -> None:
    """Een medewerker kan foto- en persoonsgegevens als JSON downloaden."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()
    photo = photo_repository.add(
        Photo(
            mm_id="MM-EXPORT-001",
            photo_number="A99501",
            publication_status=PublicationStatus.CONCEPT,
            local_subject="Voetbalvereniging",
            local_date="1962",
            local_location="Vortum-Mullem",
            local_description="Elftalfoto",
        )
    )
    photo_repository.save()
    person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.30,
        current_name="Jan Peters",
    )
    person_repository.save()
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://example.test/photo.dzi",
            "subject": "Schoolklas",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "Groepsfoto",
        },
    )

    response = client.get(f"/api/photos/{photo.id}/export.json")

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="A99501_FNO.json"'
    )
    payload = response.get_json()
    assert payload["photo"]["photo_number"] == "A99501"
    assert payload["persons"][0]["name"] == "Jan Peters"
    assert payload["comments"] == []


def test_employee_can_export_all_data_as_csv(
    client,
    app,
    authenticated_employee,
    monkeypatch,
) -> None:
    """Een medewerker kan alle voor MM bruikbare gegevens als CSV downloaden."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()
    comment_repository = CommentRepository()
    photo = photo_repository.add(
        Photo(
            mm_id="MM-EXPORT-002",
            photo_number="A99502",
            publication_status=PublicationStatus.CONCEPT,
            local_subject="Schoolklas",
            local_date="1954",
            local_location="Vortum-Mullem",
            local_description="Groepsfoto",
        )
    )
    photo_repository.save()
    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.30,
        current_name="Anna Jansen",
    )
    person_repository.save()
    comment_repository.create(
        photo_id=photo.id,
        person_id=person.id,
        author_type=AuthorType.EMPLOYEE,
        content="Waarschijnlijk de onderwijzeres.",
    )
    comment_repository.save()
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://example.test/photo.dzi",
            "subject": "Schoolklas",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "Groepsfoto",
        },
    )

    response = client.get(f"/api/photos/{photo.id}/export.csv")

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="A99502_gegevens.csv"'
    )
    content = response.get_data(as_text=True)
    assert "onderwerp" in content
    assert "Schoolklas" in content
    assert "1954" in content
    assert "Vortum-Mullem" in content
    assert "Anna Jansen" in content
    assert "Waarschijnlijk de onderwijzeres." in content
    assert "x_positie" not in content
    assert "y_positie" not in content


def test_employee_can_export_all_data_as_text(
    client,
    app,
    authenticated_employee,
    monkeypatch,
) -> None:
    """Een medewerker kan een leesbare MM-tekstexport downloaden."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()
    photo = photo_repository.add(
        Photo(
            mm_id="MM-EXPORT-003",
            photo_number="A99503",
            publication_status=PublicationStatus.CONCEPT,
            local_subject="Voetbalvereniging",
            local_date="1962",
            local_location="Vortum-Mullem",
            local_description="Elftalfoto",
        )
    )
    photo_repository.save()
    person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.30,
        current_name="Piet Peters",
    )
    person_repository.save()
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://example.test/photo.dzi",
            "subject": "Voetbalvereniging",
            "date": "1962",
            "location": "Vortum-Mullem",
            "description": "Elftalfoto",
        },
    )

    response = client.get(f"/api/photos/{photo.id}/export.txt")

    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="A99503_gegevens.txt"'
    )
    content = response.get_data(as_text=True)
    assert "Onderwerp: Voetbalvereniging" in content
    assert "Datering: 1962" in content
    assert "Locatie: Vortum-Mullem" in content
    assert "Beschrijving:" in content
    assert "Elftalfoto" in content
    assert "1. Piet Peters" in content


def test_visitor_cannot_export_photo_data(client) -> None:
    """Een bezoeker kan geen beheerexports downloaden."""

    assert client.get("/api/photos/1/export.json").status_code in {302, 401, 403}
    assert client.get("/api/photos/1/export.csv").status_code in {302, 401, 403}
    assert client.get("/api/photos/1/export.txt").status_code in {302, 401, 403}


def test_auto_label_requires_supported_image_type(
    client,
    authenticated_employee,
) -> None:
    """Auto label weigert uploads die geen JPEG of PNG zijn."""

    response = client.post(
        "/api/photos/1/auto-label",
        data={"image": (BytesIO(b"text"), "photo.txt", "text/plain")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "PERSON_DETECTION_IMAGE_TYPE_INVALID"


def test_auto_label_requires_image_upload(
    client,
    authenticated_employee,
) -> None:
    """Auto label vereist een daadwerkelijk afbeeldingsbestand."""

    response = client.post(
        "/api/photos/1/auto-label",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["code"] == "PERSON_DETECTION_IMAGE_REQUIRED"


def test_employee_can_change_person_display_mode(
    client, app, authenticated_employee
) -> None:
    """Een medewerker kan een foto op v.l.n.r.-weergave zetten."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-DISPLAY-001",
            photo_number="A99701",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.patch(
        f"/api/photos/{photo.id}/person-display-mode",
        json={"person_display_mode": "left_to_right", "person_display_count": 2},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "id": photo.id,
        "person_display_mode": "left_to_right",
        "person_display_count": 2,
    }
    assert repository.get(photo.id).person_display_mode == "left_to_right"


def test_visitor_cannot_change_person_display_mode(client, app) -> None:
    """Een bezoeker kan de personenweergave niet wijzigen."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-DISPLAY-002",
            photo_number="A99702",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.patch(
        f"/api/photos/{photo.id}/person-display-mode",
        json={"person_display_mode": "left_to_right"},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 401


def test_admin_can_delete_photo_from_fno(client, app, authenticated_admin) -> None:
    """Een beheerder kan een foto uitsluitend uit FNO verwijderen."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-DELETE-001",
            photo_number="A99801",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 204
    assert repository.get(photo.id) is None


def test_employee_cannot_delete_photo_from_fno(
    client, app, authenticated_employee
) -> None:
    """Alleen een beheerder mag een foto uit FNO verwijderen."""

    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id="MM-DELETE-002",
            photo_number="A99802",
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    response = client.delete(
        f"/api/photos/{photo.id}",
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 403
    assert repository.get(photo.id) is not None


def test_left_to_right_text_export_uses_position_order(
    client,
    app,
    authenticated_employee,
    monkeypatch,
) -> None:
    """Een v.l.n.r.-export gebruikt de horizontale positie in plaats van nummers."""

    photo_repository = PhotoRepository()
    person_repository = PersonRepository()
    photo = photo_repository.add(
        Photo(
            mm_id="MM-EXPORT-VLNR-001",
            photo_number="A99510",
            publication_status=PublicationStatus.CONCEPT,
            person_display_mode="left_to_right",
        )
    )
    photo_repository.save()
    person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.80,
        y_position=0.30,
        current_name="Rechts",
    )
    person_repository.create(
        photo_id=photo.id,
        label_number=2,
        x_position=0.20,
        y_position=0.30,
        current_name="Links",
    )
    person_repository.save()
    monkeypatch.setattr(
        "app.services.memorix_service.MemorixService.get_photo_data",
        lambda self, mm_id: {
            "image_source": "https://example.test/photo.dzi",
            "subject": "Groepsfoto",
            "date": "1954",
            "location": "Vortum-Mullem",
            "description": "",
        },
    )

    response = client.get(f"/api/photos/{photo.id}/export.txt")

    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "Personen (v.l.n.r.):" in content
    assert content.index("Links") < content.index("Rechts")
    assert "1. Rechts" not in content
