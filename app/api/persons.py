"""REST API voor personen en fotolabels."""

from __future__ import annotations

from flask import Blueprint
from flask_login import current_user

from app.api.responses import api_list_response, api_response
from app.api.validation import parse_json_request
from app.auth.decorators import admin_required, contributor_required, employee_required
from app.enums.author_type import AuthorType
from app.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    PersonCommentTextResponse,
    PersonCommentTextUpdate,
    PersonLockUpdate,
    PersonNameUpdate,
    PersonNumberUpdate,
    PersonPositionUpdate,
    PersonResponse,
)
from app.services import AuthorizationService, CommentService, PersonService

persons_blueprint = Blueprint("persons", __name__, url_prefix="/api/persons")


@persons_blueprint.patch("/<int:person_id>/position")
@employee_required
def update_person_position(person_id: int):
    """Wijzig de relatieve positie van een persoonslabel."""

    payload = parse_json_request(PersonPositionUpdate)
    person = PersonService().move_label(
        person_id=person_id,
        x_position=payload.x_position,
        y_position=payload.y_position,
    )
    return api_response(PersonResponse, person)


@persons_blueprint.patch("/<int:person_id>/number")
@employee_required
def update_person_number(person_id: int):
    """Hernummer een persoonslabel."""

    payload = parse_json_request(PersonNumberUpdate)
    person = PersonService().renumber_label(
        person_id=person_id,
        new_label_number=payload.label_number,
    )
    return api_response(PersonResponse, person)


@persons_blueprint.patch("/<int:person_id>/name")
@contributor_required
def update_person_name(person_id: int):
    """Wijzig de actuele naam van een persoon."""

    payload = parse_json_request(PersonNameUpdate)
    person = PersonService().rename_person(
        person_id=person_id,
        new_name=payload.current_name,
        user_id=current_user.id if current_user.is_authenticated else None,
        can_override_lock=AuthorizationService().can_manage_labels(),
    )
    return api_response(PersonResponse, person)


@persons_blueprint.patch("/<int:person_id>/name-lock")
@admin_required
def update_person_name_lock(person_id: int):
    """Vergrendel of ontgrendel een persoonsnaam."""

    payload = parse_json_request(PersonLockUpdate)
    person = PersonService().set_name_lock(
        person_id=person_id,
        name_locked=payload.name_locked,
        user_id=current_user.id,
    )
    return api_response(PersonResponse, person)


@persons_blueprint.get("/<int:person_id>/comments")
def get_person_comments(person_id: int):
    """Geef de opmerkingen van een persoon terug."""

    return api_list_response(
        CommentResponse,
        CommentService().get_by_person(person_id),
    )


@persons_blueprint.post("/<int:person_id>/comments")
@contributor_required
def create_person_comment(person_id: int):
    """Voeg een opmerking aan een persoon toe."""

    payload = parse_json_request(CommentCreate)
    comment = CommentService().create_person_comment(
        person_id=person_id,
        content=payload.content,
        author_type=AuthorType(current_user.role.name),
        user_id=current_user.id,
    )
    return api_response(CommentResponse, comment, status_code=201)


@persons_blueprint.patch("/<int:person_id>/comments-text")
@contributor_required
def update_person_comment_text(person_id: int):
    """Sla de doorlopende opmerkingstekst van een persoon op."""

    payload = parse_json_request(PersonCommentTextUpdate)
    content = CommentService().set_person_comment_text(
        person_id=person_id,
        content=payload.content,
        user_id=current_user.id,
        author_type=AuthorType(current_user.role.name),
    )
    response = PersonCommentTextResponse(
        person_id=person_id,
        content=content,
        has_comment=bool(content),
    )
    return api_response(PersonCommentTextResponse, response)


@persons_blueprint.delete("/<int:person_id>")
@employee_required
def delete_person_label(person_id: int):
    """Verwijder een persoonslabel."""

    PersonService().delete_label(person_id=person_id)
    return "", 204


@persons_blueprint.delete("/comments/<int:comment_id>")
@contributor_required
def delete_person_comment(comment_id: int):
    """Verwijder een opmerking administratief."""

    CommentService().delete_comment(
        comment_id=comment_id,
        user_id=current_user.id,
    )
    return "", 204


@persons_blueprint.patch("/comments/<int:comment_id>")
@contributor_required
def update_person_comment(comment_id: int):
    """Wijzig de inhoud van een opmerking."""

    payload = parse_json_request(CommentUpdate)
    comment = CommentService().update_comment(
        comment_id=comment_id,
        content=payload.content,
        user_id=current_user.id,
    )
    return api_response(CommentResponse, comment)
