"""Regressietests voor de v1.0-fotopagina-afronding."""

from app.enums.publication_status import PublicationStatus
from app.models.photo import Photo
from app.repositories.photo_repository import PhotoRepository
from app.services.photo_service import PhotoService


def _create_photo(*, mm_id: str, photo_number: str) -> Photo:
    repository = PhotoRepository()
    photo = repository.add(
        Photo(
            mm_id=mm_id,
            photo_number=photo_number,
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()
    return photo


def test_photo_defaults_to_label_size_14(app) -> None:
    """Nieuwe foto's gebruiken standaard labelgrootte 14."""

    photo = _create_photo(mm_id="MM-LABEL-SIZE-001", photo_number="LS001")

    assert photo.label_size == 14


def test_photo_service_saves_label_size_per_photo(app) -> None:
    """Labelgrootte wordt onafhankelijk per foto opgeslagen."""

    first = _create_photo(mm_id="MM-LABEL-SIZE-002", photo_number="LS002")
    second = _create_photo(mm_id="MM-LABEL-SIZE-003", photo_number="LS003")
    service = PhotoService()

    service.update_label_size(first.id, label_size=30)

    assert service.get_required(first.id).label_size == 30
    assert service.get_required(second.id).label_size == 14


def test_employee_can_change_photo_label_size(
    client,
    app,
    authenticated_employee,
) -> None:
    """Een medewerker kan de labelgrootte binnen de toegestane grenzen wijzigen."""

    photo = _create_photo(mm_id="MM-LABEL-SIZE-004", photo_number="LS004")

    response = client.patch(
        f"/api/photos/{photo.id}/label-size",
        json={"label_size": 5},
        headers={"X-CSRFToken": "test-csrf-token"},
    )

    assert response.status_code == 200
    assert response.get_json()["label_size"] == 5


def test_photo_page_has_extended_label_slider_and_single_person_option(
    client,
    authenticated_employee,
) -> None:
    """De fotopagina biedt labelgroottes 5-30 en de modus 1 persoon."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'min="5"' in response.data
    assert b'max="30"' in response.data
    assert b'value="single_person"' in response.data
    assert b">1 persoon<" in response.data


def test_visitor_no_person_css_keeps_comments_visible(client) -> None:
    """Alleen het personenpaneel verdwijnt voor bezoekers zonder labels."""

    response = client.get("/static/css/app.css")

    assert response.status_code == 200
    assert b".photo-page--visitor-no-persons .persons-panel" in response.data
    assert b".photo-page--visitor-no-persons .comments-panel" not in response.data


def test_non_numbered_modes_hide_number_column(client) -> None:
    """Niet-genummerde modi verbergen de nummerkolom in de namenlijst."""

    response = client.get("/static/js/persons.js")

    assert response.status_code == 200
    assert b'const showNumbers = displayMode === "numbered"' in response.data
    assert b'if (displayMode !== "numbered")' in response.data
