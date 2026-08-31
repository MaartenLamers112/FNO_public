"""Regressietests voor de laatste fotopagina-polish van v1.0."""

from app.models import Photo
from app.repositories import PhotoRepository
from app.services.photo_service import PhotoService


def test_photo_defaults_to_one_display_person(app) -> None:
    """Nieuwe foto's starten met één opgeslagen personenregel."""

    with app.app_context():
        repository = PhotoRepository()
        photo = repository.add(Photo(mm_id="MM-COUNT-001", photo_number="COUNT-001"))
        repository.save()

        assert photo.person_display_count == 1


def test_left_to_right_display_count_is_saved(app) -> None:
    """v.l.n.r. bewaart het gekozen aantal personen per foto."""

    with app.app_context():
        repository = PhotoRepository()
        photo = repository.add(Photo(mm_id="MM-COUNT-002", photo_number="COUNT-002"))
        repository.save()

        updated = PhotoService().update_person_display_mode(
            photo.id,
            person_display_mode="left_to_right",
            person_display_count=4,
        )

        assert updated.person_display_mode == "left_to_right"
        assert updated.person_display_count == 4


def test_photo_template_contains_count_and_numeric_label_size(
    client, authenticated_employee
) -> None:
    """De fotopagina bevat v.l.n.r.-aantal en invoerbare labelgrootte."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="person-display-count-select"' in response.data
    assert b'id="label-size-value"' in response.data
    assert b'type="number"' in response.data
    assert b"Van links naar rechts" in response.data


def test_left_to_right_hides_internal_photo_labels(
    client, authenticated_employee
) -> None:
    """v.l.n.r. toont ook voor medewerkers geen nummerlabels op de foto."""

    controller = client.get("/static/js/photo-page-controller.js")

    assert (
        b"showInternalNumbers: this.canManageLabels && "
        b'this.personDisplayMode === "numbered"' in controller.data
    )


def test_person_count_control_hidden_css_is_explicit(
    client, authenticated_employee
) -> None:
    """De aantalkeuze kan buiten v.l.n.r. echt verborgen worden."""

    stylesheet = client.get("/static/css/app.css")

    assert b".person-display-count-control[hidden]" in stylesheet.data
    assert b"display: none;" in stylesheet.data
