"""REST API voor gebruikersbeheer."""

from __future__ import annotations

from flask import Blueprint
from flask_login import current_user, login_required

from app.api.responses import api_list_response, api_response
from app.api.validation import parse_json_request
from app.auth.decorators import admin_required
from app.schemas import (
    OwnPasswordUpdate,
    UserCreate,
    UserPasswordReset,
    UserResponse,
    UserUpdate,
)
from app.services import UserService

users_blueprint = Blueprint("users", __name__, url_prefix="/api/users")


def _response_data(user) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "email_verified": user.email_verified,
        "role": user.role.name,
        "is_active": user.is_active,
    }


@users_blueprint.get("")
@admin_required
def get_users():
    """Geef alle gebruikers terug aan een beheerder."""

    return api_list_response(
        UserResponse,
        (_response_data(user) for user in UserService().list_users()),
    )


@users_blueprint.post("")
@admin_required
def create_user():
    """Maak een gebruiker aan."""

    payload = parse_json_request(UserCreate)
    user = UserService().create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        role_name=payload.role,
    )
    return api_response(UserResponse, _response_data(user), status_code=201)


@users_blueprint.patch("/<int:user_id>")
@admin_required
def update_user(user_id: int):
    """Wijzig een gebruikersaccount."""

    payload = parse_json_request(UserUpdate)
    user = UserService().update_user(
        user_id,
        username=payload.username,
        role_name=payload.role,
        is_active=payload.is_active,
        acting_user_id=current_user.id,
    )
    return api_response(UserResponse, _response_data(user))


@users_blueprint.post("/<int:user_id>/reset-password")
@admin_required
def reset_user_password(user_id: int):
    """Stel een nieuw wachtwoord voor een gebruiker in."""

    payload = parse_json_request(UserPasswordReset)
    user = UserService().reset_password(user_id, password=payload.password)
    return api_response(UserResponse, _response_data(user))


@users_blueprint.post("/me/password")
@login_required
def change_own_password():
    """Wijzig het wachtwoord van de ingelogde gebruiker."""

    payload = parse_json_request(OwnPasswordUpdate)
    user = UserService().change_own_password(
        current_user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return api_response(UserResponse, _response_data(user))
