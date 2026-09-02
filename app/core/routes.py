"""Webroutes voor de gebruikersinterface."""

from __future__ import annotations

import csv
import io
from datetime import datetime, time

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user

from app.auth.decorators import admin_required, employee_required
from app.exceptions import FNOError
from app.services import (
    DashboardService,
    HistoryService,
    MemorixParserAnalysisService,
    MmComparisonReportService,
    MmImportService,
    PhotoService,
    UserService,
)

web_blueprint = Blueprint("web", __name__)


@web_blueprint.get("/")
def index():
    """Toon de startpagina."""

    return render_template("index.html", help_context="overview")


@web_blueprint.get("/photos/<int:photo_id>")
def photo_page(photo_id: int):
    """Stuur een bestaande technische ID-link door naar het fotonummer."""

    photo = PhotoService().get(photo_id)
    if photo is None:
        return render_template("photo.html", photo_id=photo_id, help_context="photo")

    return redirect(
        url_for(
            "web.photo_page_by_number",
            photo_number=photo.photo_number,
        )
    )


@web_blueprint.get("/photos/<photo_number>")
def photo_page_by_number(photo_number: str):
    """Toon de fotopagina via het stabiele fotonummer."""

    photo = PhotoService().get_by_photo_number(photo_number)
    if photo is None:
        return render_template("photo.html", photo_id=0, help_context="photo"), 404

    return render_template("photo.html", photo_id=photo.id, help_context="photo")


@web_blueprint.get("/admin")
@employee_required
def admin_dashboard():
    """Toon het dashboard voor medewerkers en beheerders."""

    summary = DashboardService().get_summary()
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        help_context="admin",
    )


@web_blueprint.route("/admin/photos/import", methods=["GET", "POST"])
@admin_required
def admin_import_photos():
    """Zoek en importeer foto's uit Maior Memorix."""

    filters = {
        key: request.form.get(key, "")
        for key in (
            "collection_part",
            "collection",
            "place",
            "subject",
            "title",
            "description",
            "photo_number",
            "date",
        )
    }
    preview = None
    import_job = None
    requested_page = request.form.get("page_target", type=int)
    if requested_page is None:
        requested_page = request.form.get("page", 1, type=int)
    page = max(requested_page or 1, 1)
    service = MmImportService()
    action = request.form.get("action") if request.method == "POST" else None

    if action == "parser_analysis":
        try:
            analysis_rows = MemorixParserAnalysisService().analyze(filters)
            output = io.StringIO()
            writer = csv.writer(output, delimiter=";")
            writer.writerow([
                "Categorie",
                "Betrouwbaar",
                "Parserreden",
                "Patroongroep",
                "Aantal genummerde items",
                "Kandidaat-items",
                "Onbekende posities",
                "Lijstopmaak",
                "Namenkop aanwezig",
                "Waarschuwingssignalen",
                "MM ID",
                "Fotonummer",
                "Aantal namen",
                "Gevonden namen",
                "Beschrijving na parser",
                "Originele MM-beschrijving",
            ])
            for row in analysis_rows:
                writer.writerow([
                    row.category,
                    "ja" if row.reliable else "nee",
                    row.reason,
                    row.pattern_group,
                    row.numbered_items_count,
                    row.candidate_items,
                    row.unknown_positions_count,
                    row.list_layout,
                    "ja" if row.has_name_header else "nee",
                    row.warning_signals,
                    row.mm_id,
                    row.photo_number,
                    row.names_count,
                    row.names,
                    row.parsed_description,
                    row.original_description,
                ])
            filename = (
                f"mm_parseranalyse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            return Response(
                "\ufeff" + output.getvalue(),
                content_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except FNOError as error:
            flash(str(error), "error")
            return redirect(url_for("web.admin_import_photos"))

    if action == "comparison_report":
        try:
            report = MmComparisonReportService().build_xlsx()
            filename = (
                f"mm_vergelijkrapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            return Response(
                report,
                content_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except FNOError as error:
            flash(str(error), "error")
            return redirect(url_for("web.admin_import_photos"))

    try:
        filter_options = service.get_filter_options()
    except FNOError as error:
        flash(str(error), "error")
        filter_options = {}

    if request.method == "POST":
        try:
            if action == "import":
                selected_mm_ids = set(request.form.getlist("selected_mm_ids"))
                import_job = service.import_selected(
                    filters=filters,
                    selected_mm_ids=selected_mm_ids,
                    user_id=current_user.id,
                    page=page,
                )
                flash(
                    f"{import_job.imported_count} foto's zijn als concept toegevoegd; "
                    f"{import_job.skipped_count} bestonden al en "
                    f"{import_job.failed_count} konden niet worden geïmporteerd.",
                    "success",
                )
            elif action == "supplement":
                result = service.supplement_missing_metadata(user_id=current_user.id)
                flash(
                    f"{result.checked_photos} FNO-foto's gecontroleerd; "
                    f"{result.updated_fields} lege velden bij "
                    f"{result.updated_photos} foto's aangevuld vanuit MM. "
                    f"{result.missing_photos} foto's zijn niet in de "
                    "MM-zoekset gevonden.",
                    "success",
                )
                return redirect(url_for("web.admin_import_photos"))
            preview = service.preview(filters, page=page)
        except FNOError as error:
            flash(str(error), "error")

    return render_template(
        "admin/import_photos.html",
        filters=filters,
        preview=preview,
        filter_options=filter_options,
        import_job=import_job,
        help_context="admin",
    )


@web_blueprint.route("/admin/users", methods=["GET", "POST"])
@admin_required
def admin_users():
    """Beheer medewerkers en beheerders."""

    service = UserService()
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "create":
                service.create_user(
                    username=request.form.get("username", ""),
                    password=request.form.get("password", ""),
                    role_name=request.form.get("role", ""),
                )
                flash("Gebruiker aangemaakt.", "success")
            elif action == "update":
                service.update_user(
                    int(request.form.get("user_id", "0")),
                    username=request.form.get("username", ""),
                    role_name=request.form.get("role", ""),
                    is_active=request.form.get("is_active") == "on",
                    acting_user_id=current_user.id,
                )
                flash("Gebruiker bijgewerkt.", "success")
            elif action == "reset_password":
                service.reset_password(
                    int(request.form.get("user_id", "0")),
                    password=request.form.get("password", ""),
                )
                flash("Wachtwoord opnieuw ingesteld.", "success")
        except (FNOError, ValueError) as error:
            flash(str(error), "error")
        return redirect(url_for("web.admin_users"))

    return render_template(
        "admin/users.html",
        users=service.list_users(),
        help_context="admin",
    )


@web_blueprint.get("/privacy")
def privacy_page():
    """Toon de privacy- en AVG-informatie."""

    return render_template("privacy.html", help_context="privacy")


@web_blueprint.get("/disclaimer")
def disclaimer_page():
    """Toon de disclaimer van FNO."""

    return render_template("disclaimer.html", help_context="disclaimer")


@web_blueprint.get("/contact")
def contact_page():
    """Toon contactmogelijkheden voor vragen en correcties."""

    return render_template("contact.html", help_context="contact")


def _history_filters():
    def parse_date(value: str, *, end: bool = False):
        if not value:
            return None
        date = datetime.strptime(value, "%Y-%m-%d").date()
        return datetime.combine(date, time.max if end else time.min)

    return {
        "photo_number": request.args.get("photo_number", "").strip(),
        "event_type": request.args.get("event_type", "").strip(),
        "username": request.args.get("username", "").strip(),
        "started_at": parse_date(request.args.get("started_at", "")),
        "ended_at": parse_date(request.args.get("ended_at", ""), end=True),
    }


@web_blueprint.get("/admin/history")
@employee_required
def admin_history():
    """Toon het volledige wijzigingsarchief."""
    filters = _history_filters()
    items = HistoryService().search(**filters)
    return render_template(
        "admin/history.html",
        items=items,
        filters=request.args,
        help_context="admin",
    )


@web_blueprint.get("/admin/history.csv")
@employee_required
def admin_history_csv():
    """Exporteer het gefilterde wijzigingsarchief als CSV."""
    items = HistoryService().search(**_history_filters())
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "Datum/tijd",
        "Fotonummer",
        "Gebruiker",
        "Wijzigingstype",
        "Omschrijving",
        "Oude waarde",
        "Nieuwe waarde",
    ])
    for item in items:
        writer.writerow([
            item.created_at.strftime("%d-%m-%Y %H:%M:%S"),
            item.photo.photo_number,
            item.user.username if item.user else "",
            item.event_type,
            item.description,
            item.old_value or "",
            item.new_value or "",
        ])
    filename = f"FNO_historie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
