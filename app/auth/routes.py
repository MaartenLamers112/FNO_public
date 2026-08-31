"""Webroutes voor authenticatie."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.exceptions import AuthorizationError, ValidationError
from app.services import UserService

auth_blueprint = Blueprint(
    "auth",
    __name__,
)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Meld een medewerker of beheerder aan."""

    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        try:
            user = UserService().authenticate(
                username=request.form.get("username", ""),
                password=request.form.get("password", ""),
            )
        except (AuthorizationError, ValidationError) as error:
            flash(str(error), "error")
        else:
            login_user(user)
            return redirect(_safe_next_url(next_url) or url_for("web.index"))

    return render_template(
        "login.html",
        next_url=next_url or "",
    )


@auth_blueprint.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Laat een ingelogde gebruiker het eigen wachtwoord wijzigen."""

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirmation = request.form.get("new_password_confirmation", "")
        if new_password != confirmation:
            flash("De nieuwe wachtwoorden zijn niet gelijk.", "error")
        else:
            try:
                UserService().change_own_password(
                    current_user.id,
                    current_password=request.form.get("current_password", ""),
                    new_password=new_password,
                )
            except (AuthorizationError, ValidationError) as error:
                flash(str(error), "error")
            else:
                flash("Je wachtwoord is gewijzigd.", "success")
                return redirect(url_for("web.index"))

    return render_template("change_password.html", help_context="overview")


@auth_blueprint.post("/logout")
@login_required
def logout():
    """Meld de huidige gebruiker af."""

    logout_user()
    flash("Je bent afgemeld.", "success")

    return redirect(url_for("web.index"))


def _safe_next_url(target: str | None) -> str | None:
    """Geef alleen een lokale doorstuur-URL terug."""

    if not target:
        return None

    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))

    if redirect_url.scheme not in {"http", "https"}:
        return None

    if redirect_url.netloc != host_url.netloc:
        return None

    return redirect_url.path + (f"?{redirect_url.query}" if redirect_url.query else "")
