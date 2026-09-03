"""REST API voor foto's."""

from __future__ import annotations

import json

from flask import Blueprint, Response, request
from flask_login import current_user

from app.api.responses import api_list_response, api_response
from app.api.validation import parse_json_request, parse_query_request
from app.auth.decorators import (
    admin_required,
    contributor_required,
    employee_required,
    publication_management_required,
)
from app.exceptions import ValidationError
from app.schemas import (
    AutoLabelResponse,
    CommentResponse,
    PersonCreate,
    PersonResponse,
    PhotoCollectionResponse,
    PhotoDetailResponse,
    PhotoExportResponse,
    PhotoLabelSizeResponse,
    PhotoLabelSizeUpdate,
    PhotoListQuery,
    PhotoManagementUpdate,
    PhotoMetadataUpdate,
    PhotoPersonDisplayModeResponse,
    PhotoPersonDisplayModeUpdate,
    PhotoPublicationStatusUpdate,
    PhotoPublicCollectionResponse,
    PhotoPublicDetailResponse,
    PhotoResponse,
)
from app.services import (
    AuthorizationService,
    CommentService,
    ExportService,
    PersonDetectionService,
    PersonService,
    PhotoService,
)

photos_blueprint = Blueprint(
    "photos",
    __name__,
    url_prefix="/api/photos",
)


@photos_blueprint.get("")
def get_photos():
    """Geef foto's voor de landingspagina terug."""

    query = parse_query_request(PhotoListQuery)
    service = PhotoService()

    authorization = AuthorizationService()
    can_view_comparison = authorization.can_manage_labels()
    can_view_hidden = authorization.can_view_hidden_photos()
    return api_response(
        (
            PhotoCollectionResponse
            if can_view_comparison
            else PhotoPublicCollectionResponse
        ),
        service.get_landing_page(
            search=query.search,
            status=query.status,
            location=query.location,
            sort=query.sort,
            direction=query.direction,
            visible_only=not can_view_hidden,
            include_comparison=can_view_comparison,
        ),
    )


@photos_blueprint.get("/<int:photo_id>")
def get_photo(
    photo_id: int,
):
    """Geef één foto met live afbeeldingsbron terug."""

    service = PhotoService()
    authorization = AuthorizationService()
    can_view_comparison = authorization.can_manage_labels()
    can_view_hidden = authorization.can_view_hidden_photos()
    detail = service.get_accessible_detail(
        photo_id,
        include_hidden=can_view_hidden,
        include_comparison=can_view_comparison,
    )
    schema = PhotoDetailResponse if can_view_comparison else PhotoPublicDetailResponse
    return api_response(schema, detail)


@photos_blueprint.patch("/<int:photo_id>/metadata")
@contributor_required
def update_photo_metadata(photo_id: int):
    """Wijzig lokale FNO-metadata van een foto."""

    payload = parse_json_request(PhotoMetadataUpdate)
    photo = PhotoService().update_local_metadata(
        photo_id,
        subject=payload.subject,
        date=payload.date,
        location=payload.location,
        description=payload.description,
        user_id=current_user.id if current_user.is_authenticated else None,
    )
    return api_response(PhotoResponse, photo)


@photos_blueprint.patch("/<int:photo_id>/management")
@publication_management_required
def update_photo_management(photo_id: int):
    """Wijzig zichtbaarheid en gereedmelding van een foto."""

    payload = parse_json_request(PhotoManagementUpdate)
    photo = PhotoService().update_management(
        photo_id,
        is_visible=payload.is_visible,
        is_complete=payload.is_complete,
        user_id=current_user.id,
    )
    return api_response(
        PhotoResponse,
        {
            "id": photo.id,
            "mm_id": photo.mm_id,
            "photo_number": photo.photo_number,
            "publication_status": photo.publication_status,
            "progress_status": PhotoService().get_progress_status(photo),
            "is_visible": photo.is_visible,
            "is_complete": photo.is_complete,
        },
    )


@photos_blueprint.patch("/<int:photo_id>/person-display-mode")
@employee_required
def update_photo_person_display_mode(photo_id: int):
    """Wijzig de personenweergave van een foto."""

    payload = parse_json_request(PhotoPersonDisplayModeUpdate)
    photo = PhotoService().update_person_display_mode(
        photo_id,
        person_display_mode=payload.person_display_mode,
        person_display_count=payload.person_display_count,
        user_id=current_user.id,
    )
    return api_response(
        PhotoPersonDisplayModeResponse,
        {
            "id": photo.id,
            "person_display_mode": photo.person_display_mode,
            "person_display_count": photo.person_display_count,
        },
    )


@photos_blueprint.patch("/<int:photo_id>/label-size")
@employee_required
def update_photo_label_size(photo_id: int):
    """Wijzig de labelgrootte van een foto."""

    payload = parse_json_request(PhotoLabelSizeUpdate)
    photo = PhotoService().update_label_size(
        photo_id,
        label_size=payload.label_size,
        user_id=current_user.id,
    )
    return api_response(
        PhotoLabelSizeResponse,
        {"id": photo.id, "label_size": photo.label_size},
    )


@photos_blueprint.delete("/<int:photo_id>")
@admin_required
def delete_photo_from_fno(photo_id: int):
    """Verwijder een foto uitsluitend uit FNO."""

    PhotoService().delete_from_fno(photo_id)
    return "", 204


@photos_blueprint.patch("/<int:photo_id>/publication-status")
@publication_management_required
def update_photo_publication_status(photo_id: int):
    """Wijzig de publicatiestatus van een foto."""

    payload = parse_json_request(PhotoPublicationStatusUpdate)
    photo = PhotoService().set_publication_status(
        photo_id,
        payload.publication_status,
        user_id=current_user.id,
    )

    return api_response(PhotoResponse, photo)


@photos_blueprint.post("/<int:photo_id>/auto-label")
@employee_required
def auto_label_photo(photo_id: int):
    """Maak echte labels op basis van de door de browser getoonde foto."""

    upload = request.files.get("image")
    if upload is None or not upload.filename:
        raise ValidationError(
            "De afbeelding voor Auto label ontbreekt.",
            code="PERSON_DETECTION_IMAGE_REQUIRED",
        )
    if upload.mimetype not in {"image/jpeg", "image/png"}:
        raise ValidationError(
            "Auto label ondersteunt alleen JPEG- en PNG-afbeeldingen.",
            code="PERSON_DETECTION_IMAGE_TYPE_INVALID",
        )

    image_bytes = upload.read()
    result = PersonDetectionService().auto_label(
        photo_id=photo_id,
        image_bytes=image_bytes,
        user_id=current_user.id,
    )
    return api_response(AutoLabelResponse, result, status_code=201)


@photos_blueprint.get("/<int:photo_id>/export.json")
@employee_required
def export_photo_json(photo_id: int):
    """Download actuele FNO-fotogegevens als JSON."""

    export = ExportService().get_photo_export(photo_id)
    payload = PhotoExportResponse.model_validate(export).model_dump(mode="json")
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    filename = f"{export.photo['photo_number']}_FNO.json"

    return Response(
        content,
        mimetype="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@photos_blueprint.get("/<int:photo_id>/export.csv")
@employee_required
def export_photo_csv(photo_id: int):
    """Download alle voor MM bruikbare ingevulde gegevens als CSV."""

    service = ExportService()
    photo = PhotoService().get_required(photo_id)
    content = "\ufeff" + service.create_data_csv(photo_id)
    filename = f"{photo.photo_number}_gegevens.csv"

    return Response(
        content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@photos_blueprint.get("/<int:photo_id>/export.txt")
@employee_required
def export_photo_text(photo_id: int):
    """Download een leesbare tekstexport voor verwerking in MM."""

    service = ExportService()
    photo = PhotoService().get_required(photo_id)
    content = "\ufeff" + service.create_text_export(photo_id)
    filename = f"{photo.photo_number}_gegevens.txt"

    return Response(
        content,
        mimetype="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@photos_blueprint.post("/<int:photo_id>/persons/renumber")
@employee_required
def renumber_photo_persons(photo_id: int):
    """Hernummer labels in leesvolgorde op de foto."""

    persons = PersonService().renumber_by_position(
        photo_id=photo_id,
        user_id=current_user.id,
    )
    return api_list_response(PersonResponse, persons)


@photos_blueprint.post("/<int:photo_id>/persons")
@employee_required
def create_photo_person(
    photo_id: int,
):
    """Maak een nieuw persoonslabel op een foto."""

    payload = parse_json_request(PersonCreate)
    service = PersonService()

    person = service.create_next_label(
        photo_id=photo_id,
        x_position=payload.x_position,
        y_position=payload.y_position,
    )

    return api_response(
        PersonResponse,
        person,
        status_code=201,
    )


@photos_blueprint.delete("/<int:photo_id>/persons")
@employee_required
def delete_all_photo_persons(photo_id: int):
    """Verwijder alle persoonslabels van één foto."""

    PersonService().delete_all_labels(
        photo_id=photo_id,
        user_id=current_user.id,
    )
    return "", 204


@photos_blueprint.get("/<int:photo_id>/persons")
def get_photo_persons(
    photo_id: int,
):
    """Geef alle persoonslabels van één foto terug."""

    service = PersonService()

    return api_list_response(
        PersonResponse,
        service.get_by_photo(photo_id),
    )


@photos_blueprint.get("/<int:photo_id>/comments")
def get_photo_comments(
    photo_id: int,
):
    """Geef alle opmerkingen van een foto."""

    service = CommentService()

    return api_list_response(
        CommentResponse,
        service.get_by_photo(photo_id),
    )
