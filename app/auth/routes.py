"""Webroutes voor authenticatie."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.exceptions import AuthorizationError, ConflictError, ValidationError
from app.services import (
    EmailVerificationService,
    PasswordResetService,
    RegistrationService,
    RoleUpgradeRequestService,
    UserService,
)

auth_blueprint = Blueprint(
    "auth",
    __name__,
)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Meld een FNO-gebruiker aan."""

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


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    """Registreer een nieuw openbaar gebruikersaccount."""

    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    if request.method == "POST":
        try:
            RegistrationService().register(
                username=request.form.get("username", ""),
                email=request.form.get("email", ""),
                password=request.form.get("password", ""),
                password_confirmation=request.form.get("password_confirmation", ""),
            )
        except (ConflictError, ValidationError) as error:
            flash(str(error), "error")
        except RuntimeError:
            flash(
                "Het account is aangemaakt, maar de verificatiemail kon niet "
                "worden verstuurd. Probeer de verificatiemail opnieuw te sturen.",
                "error",
            )
            return redirect(url_for("auth.resend_verification"))
        else:
            flash(
                "Je account is aangemaakt. Controleer je e-mail om het account "
                "te bevestigen.",
                "success",
            )
            return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_blueprint.get("/verify-email/<token>")
def verify_email(token: str):
    """Bevestig een e-mailadres via een tijdgebonden verificatielink."""

    try:
        RegistrationService().verify_email(token)
    except ValidationError as error:
        flash(str(error), "error")
        return redirect(url_for("auth.resend_verification"))

    flash("Je e-mailadres is bevestigd. Je kunt nu bijdragen aan FNO.", "success")
    return redirect(url_for("auth.login"))


@auth_blueprint.route("/verify-email/resend", methods=["GET", "POST"])
def resend_verification():
    """Stuur desgevraagd opnieuw een verificatiebericht."""

    if request.method == "POST":
        try:
            RegistrationService().resend_verification(request.form.get("email", ""))
        except RuntimeError:
            flash(
                "De verificatiemail kon niet worden verstuurd. "
                "Probeer het later opnieuw.",
                "error",
            )
        else:
            flash(
                "Als het e-mailadres bij een onbevestigd account hoort, is een "
                "nieuwe verificatiemail verstuurd.",
                "success",
            )
            return redirect(url_for("auth.login"))

    return render_template("resend_verification.html")


@auth_blueprint.route("/password/forgot", methods=["GET", "POST"])
def forgot_password():
    """Vraag zonder accountinformatie te lekken een wachtwoordlink aan."""

    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    if request.method == "POST":
        try:
            PasswordResetService().request_reset(request.form.get("email", ""))
        except RuntimeError:
            current_app.logger.exception(
                "Wachtwoordherstelmail kon niet worden verstuurd."
            )

        flash(
            "Als het e-mailadres bij een actief account hoort, is een "
            "wachtwoordlink verstuurd.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_blueprint.route("/password/reset/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    """Stel via een geldige e-maillink een nieuw wachtwoord in."""

    if current_user.is_authenticated:
        return redirect(url_for("web.index"))

    service = PasswordResetService()

    if request.method == "GET":
        try:
            service.validate_token(token)
        except ValidationError as error:
            flash(str(error), "error")
            return redirect(url_for("auth.forgot_password"))
        return render_template("reset_password.html")

    try:
        service.reset_password(
            token,
            password=request.form.get("password", ""),
            password_confirmation=request.form.get("password_confirmation", ""),
        )
    except ValidationError as error:
        flash(str(error), "error")
        return render_template("reset_password.html")

    flash("Je wachtwoord is gewijzigd. Je kunt nu aanmelden.", "success")
    return redirect(url_for("auth.login"))


@auth_blueprint.route("/account/email", methods=["GET", "POST"])
@login_required
def change_email():
    """Laat een ingelogde gebruiker het eigen e-mailadres wijzigen."""

    if request.method == "POST":
        try:
            user = UserService().change_own_email(
                current_user.id,
                email=request.form.get("email", ""),
                current_password=request.form.get("current_password", ""),
            )
        except (AuthorizationError, ConflictError, ValidationError) as error:
            flash(str(error), "error")
        else:
            try:
                EmailVerificationService().send_verification(user)
            except RuntimeError:
                current_app.logger.exception(
                    "Verificatiemail na e-mailwijziging kon niet worden verstuurd."
                )
                flash(
                    "Het nieuwe e-mailadres is opgeslagen, maar de verificatiemail "
                    "kon niet worden verstuurd. Probeer de verificatiemail opnieuw "
                    "te sturen.",
                    "error",
                )
                return redirect(url_for("auth.resend_verification"))

            flash(
                "Je nieuwe e-mailadres is opgeslagen. Controleer je e-mail om "
                "het adres opnieuw te bevestigen.",
                "success",
            )
            return redirect(url_for("web.index"))

    return render_template("change_email.html", help_context="overview")


@auth_blueprint.route("/account/role-request", methods=["GET", "POST"])
@login_required
def request_role_upgrade():
    """Laat een ingelogde gebruiker een hogere rol aanvragen."""

    service = RoleUpgradeRequestService()
    if request.method == "POST":
        try:
            service.request_upgrade(current_user.id)
        except (AuthorizationError, ValidationError) as error:
            flash(str(error), "error")
        except RuntimeError:
            current_app.logger.exception(
                "Rolverhogingsaanvraag opgeslagen, maar beheerdersmail mislukte."
            )
            flash(
                "Je aanvraag is opgeslagen, maar de e-mailmelding aan beheerders "
                "kon niet worden verstuurd.",
                "error",
            )
        else:
            flash("Je aanvraag is verstuurd naar de beheerders.", "success")
        return redirect(url_for("auth.request_role_upgrade"))

    return render_template(
        "role_upgrade_request.html",
        service=service,
        pending_request=service.get_pending_for_user(current_user.id),
        next_role=service.get_available_upgrade(current_user.id),
        help_context="overview",
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
