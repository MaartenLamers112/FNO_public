"""Tests voor de HTML-webroutes."""


def test_index_page_is_available(client) -> None:
    """De startpagina is bereikbaar."""

    response = client.get("/")

    assert response.status_code == 200
    assert b"Foto Nummeraar Online" in response.data


def test_photo_page_is_available(client) -> None:
    """De fotopagina is bereikbaar."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'data-photo-id="123"' in response.data
    assert b"photo-page.js" in response.data
    assert b'id="previous-photo-link"' in response.data
    assert b'id="next-photo-link"' in response.data
    assert b'id="toggle-label-placement"' not in response.data


def test_persons_panel_scrolls_independently(client) -> None:
    """Het personenpaneel scrolt zonder de fotopagina te verplaatsen."""

    page_response = client.get("/photos/123")
    css_response = client.get("/static/css/app.css")
    javascript_response = client.get("/static/js/persons.js")

    assert b'class="panel persons-panel"' in page_response.data
    assert b".persons-list" in css_response.data
    assert b"overflow-y: auto" in css_response.data
    assert b"scrollbar-gutter: stable" in css_response.data
    assert b"scrollIntoView" not in javascript_response.data
    assert b"list.scrollBy" in javascript_response.data


def test_photo_page_supports_label_deletion(client) -> None:
    """De fotopagina bevat bediening voor het verwijderen van een label."""

    page_response = client.get("/photos/123")
    controller_response = client.get("/static/js/photo-page-controller.js")
    api_response = client.get("/static/js/api.js")

    assert b'id="delete-person-label"' not in page_response.data
    assert b"#delete-person-label" in controller_response.data
    assert b"window.confirm" in controller_response.data
    assert b"export async function remove" in api_response.data


def test_new_label_scrolls_inside_persons_panel(client) -> None:
    """Een nieuw label wordt zichtbaar gemaakt binnen het personenpaneel."""

    response = client.get("/static/js/photo-page-controller.js")

    assert (
        b"await this.#openComments(person.id, { focusInput: false });" in response.data
    )
    assert b"ensureListItemVisible: false" not in response.data


def test_photo_page_uses_compact_metadata_and_comments(client) -> None:
    """Metadata en opmerkingen gebruiken compacte invoervelden."""

    page = client.get("/photos/123")
    css = client.get("/static/css/app.css")
    controller = client.get("/static/js/photo-page-controller.js")
    persons = client.get("/static/js/persons.js")

    assert b'id="photo-subject"' in page.data
    assert b'id="photo-date"' in page.data
    assert b'id="photo-location"' in page.data
    assert b'rows="3"' in page.data
    assert b"overflow-y: auto" in css.data
    assert b"void this.#openComments(id)" in controller.data
    assert b"person-number-arrow" in persons.data
    assert b"person.label_number - 1" in persons.data
    assert b"person.label_number + 1" in persons.data


def test_photo_page_fills_available_height(client) -> None:
    """De fotopagina gebruikt de resterende browserhoogte."""

    css = client.get("/static/css/app.css")

    assert b"height: 100vh" in css.data
    assert b"flex: 1" in css.data
    assert b"overflow: hidden" in css.data


def test_person_inputs_select_without_losing_focus(client) -> None:
    """Naam en nummer selecteren persoon en houden invoerfocus vast."""

    persons = client.get("/static/js/persons.js")
    controller = client.get("/static/js/photo-page-controller.js")

    assert b"onPersonInputSelect" in persons.data
    assert b"focusInput: false" in controller.data
    assert b"setPersonCommentState" in controller.data


def test_application_contains_global_help_dialog(client) -> None:
    """De algemene header bevat een uitbreidbare helpdialoog."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="open-help-dialog"' in response.data
    assert b'id="help-dialog"' in response.data
    assert b'id="help-welcome"' not in response.data
    assert b"help-dialog.js" in response.data
    assert b'class="keyboard-help"' not in response.data


def test_photo_page_contains_dismissible_error(client) -> None:
    """De fotopagina bevat een sluitbare foutmelding."""

    response = client.get("/photos/123")

    assert b'id="dismiss-error-message"' in response.data
    assert b'id="error-message-text"' in response.data


def test_delete_shortcut_uses_window_capture(client) -> None:
    """Delete wordt robuust op vensterniveau afgehandeld."""

    response = client.get("/static/js/photo-page-controller.js")

    assert b'window.addEventListener("keydown"' in response.data
    assert b"{ capture: true }" in response.data
    assert b'event.code === "Delete"' in response.data
    assert b"event.keyCode === 46" in response.data
    assert response.data.count(b"focusInput: false") >= 4


def test_landing_page_uses_compact_icon_view_switcher(client) -> None:
    """De weergavekeuze gebruikt iconen in de zoekwerkbalk."""

    page = client.get("/")
    javascript = client.get("/static/js/landing/index-page.js")
    theme = client.get("/static/css/theme.css")

    assert b'id="photo-result-count"' not in page.data
    assert b'<fieldset class="view-switcher">' in page.data
    assert page.data.count(b"data-view=") == 4
    assert b"<svg" in page.data
    assert b'aria-label="Kleine thumbnails"' in page.data
    assert b"count: root.querySelector" not in javascript.data
    assert b"--color-primary" in theme.data
    assert b"--header-height" in theme.data


def test_landing_page_contains_designed_views(client) -> None:
    """De landingspagina bevat drie rastergroottes en een lijstweergave."""

    page = client.get("/")
    javascript = client.get("/static/js/landing/index-page.js")
    renderer = client.get("/static/js/landing/render.js")

    assert b'id="photo-search"' in page.data
    assert b'id="photo-status-filter"' in page.data
    assert b'id="photo-location-filter"' in page.data
    assert b'data-view="small"' in page.data
    assert b'data-view="medium"' in page.data
    assert b'data-view="large"' in page.data
    assert b'data-view="list"' in page.data
    assert b"saveScrollPosition" in javascript.data
    assert b"photo-list-table" in renderer.data
    assert b"photo-progress-dot" in renderer.data


def test_keyboard_navigation_does_not_focus_comments(client) -> None:
    """Pijlnavigatie toont opmerkingen zonder het tekstveld te focussen."""

    controller = client.get("/static/js/photo-page-controller.js")

    assert (
        b"this.#openComments(persons[next].id, { focusInput: false })"
        in controller.data
    )


def test_theme_matches_village_site_visual_direction(client) -> None:
    """Het centrale thema gebruikt de afgesproken blauwe huisstijl."""

    theme = client.get("/static/css/theme.css")
    css = client.get("/static/css/app.css")

    assert b"--color-primary: #1768ad" in theme.data
    assert b"--color-heading: #07549a" in theme.data
    assert b"--header-height: 4.9rem" in theme.data
    assert b".welcome-panel," in css.data
    assert b"border: 0" in css.data
    assert b"box-shadow: var(--shadow-small)" in css.data


def test_admin_pages_can_scroll(client, authenticated_employee) -> None:
    """De beheeromgeving kan verticaal scrollen."""

    response = client.get("/admin")
    css = client.get("/static/css/app.css")

    assert response.status_code == 200
    assert b"admin-page-body" in response.data
    assert b".admin-page-body" in css.data
    assert b"overflow-y: auto" in css.data


def test_admin_dashboard_uses_shared_admin_navigation(
    client, authenticated_admin
) -> None:
    """Het dashboard gebruikt de gedeelde beheerwerkplek met tabs."""

    response = client.get("/admin")

    assert response.status_code == 200
    assert b'class="admin-tabs"' in response.data
    assert b"Dashboard" in response.data
    assert b"Import" in response.data
    assert b"Historie" in response.data


def test_import_preview_has_internal_scroll_area(client, authenticated_admin) -> None:
    """De MM-voorvertoning heeft een eigen scrollgebied."""

    css = client.get("/static/css/app.css")

    assert b"max-height: 55vh" in css.data
    assert b"position: sticky" in css.data


def test_import_preview_uses_column_filters(client) -> None:
    """De importvoorvertoning bevat filters in de tabelkop."""

    page = client.get("/static/js/admin/import-preview.js")
    template = client.get("/admin/photos/import")

    assert b"data-column-filter" in page.data
    assert b"data-status-filter" not in page.data
    assert template.status_code in {302, 401}


def test_photo_page_contains_publication_control_for_admin(
    client, authenticated_admin
) -> None:
    """Een beheerder ziet de publicatiestatusbediening op de fotopagina."""

    response = client.get("/photos/123")

    assert b'id="photo-visible"' in response.data
    assert b'id="photo-complete"' in response.data
    assert b'data-can-manage-publication="true"' in response.data


def test_landing_renderer_contains_publication_controls(client) -> None:
    """Raster en tabel kunnen publicatiestatus tonen en wijzigen."""

    response = client.get("/static/js/landing/render.js")

    assert b"createVisibilityToggle" in response.data
    assert b"createStatusDot" in response.data


def test_history_page_and_csv_are_available(client, authenticated_employee) -> None:
    """Beheer kan historie bekijken en exporteren."""
    assert client.get("/admin/history").status_code == 200
    response = client.get("/admin/history.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"


def test_contact_button_is_available(client) -> None:
    """De algemene header bevat contactinformatie."""
    response = client.get("/")
    assert b'id="open-contact-dialog"' in response.data


def test_comparison_symbols_are_role_restricted(client, authenticated_employee) -> None:
    """Alleen medewerkers zien de MM-vergelijking in de interface."""

    employee_index = client.get("/")
    employee_photo = client.get("/photos/123")

    assert b'data-can-view-comparison="true"' in employee_index.data
    assert b'data-can-view-comparison="true"' in employee_photo.data
    assert b'data-comparison-field="subject"' in employee_photo.data


def test_visitor_comparison_is_disabled_in_interface(client) -> None:
    """Bezoekers krijgen geen actieve MM-vergelijkweergave."""

    index = client.get("/")
    photo = client.get("/photos/123")

    assert b'data-can-view-comparison="false"' in index.data
    assert b'data-can-view-comparison="false"' in photo.data
    assert b"data-comparison-field=" not in photo.data


def test_photo_description_uses_autogrow_layout(client, authenticated_employee) -> None:
    """Het beschrijvingsveld start compact en ondersteunt automatisch groeien."""

    photo = client.get("/photos/123")
    script = client.get("/static/js/photo-details.js")

    assert b'id="photo-description"' in photo.data
    assert b'rows="2"' in photo.data
    assert b"resizeDescriptionField" in script.data


def test_header_uses_single_expandable_account_control(client) -> None:
    """De header gebruikt één sleutel- of initialenknop voor accountacties."""

    response = client.get("/")

    assert b'id="account-menu-toggle"' in response.data
    assert b'id="account-menu-panel"' in response.data
    assert b'name="username"' in response.data
    assert b'name="password"' in response.data
    assert b"account-menu.js" in response.data


def test_photo_status_and_management_are_in_command_row(
    client, authenticated_admin
) -> None:
    """Fotostatus en beheervelden staan bij navigatie en fotowerkbalk."""

    response = client.get("/photos/123")
    page = response.data

    navigation_start = page.index(b'class="photo-navigation"')
    toolbar_start = page.index(b'class="photo-label-toolbar"')
    sidebar_start = page.index(b'class="photo-sidebar"')

    assert navigation_start < page.index(b'id="photo-progress-dot"') < toolbar_start
    assert toolbar_start < page.index(b'id="photo-visible"') < sidebar_start
    assert toolbar_start < page.index(b'id="photo-complete"') < sidebar_start


def test_photo_navigation_uses_saved_landing_order(client) -> None:
    """Fotopijlen gebruiken de bewaarde volgorde van het actuele overzicht."""

    landing = client.get("/static/js/landing/index-page.js")
    controller = client.get("/static/js/photo-page-controller.js")
    context = client.get("/static/js/navigation-context.js")

    assert b"#updatePhotoTab(data.items)" in landing.data
    assert b"storePhotoContext(items)" in landing.data
    assert b"contextNeighbours(this.photoId)" in controller.data
    assert b"previousPhotoId" in context.data
    assert b"nextPhotoId" in context.data


def test_photo_page_contains_auto_label_control(client, authenticated_employee) -> None:
    """Medewerkers zien één knop voor automatisch labelen."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="detect-persons"' in response.data
    assert b">Auto label</button>" in response.data
    assert b'id="apply-detection-proposals"' not in response.data
    assert b'id="clear-detection-proposals"' not in response.data
    controller = client.get("/static/js/photo-page-controller.js")
    assert b"captureViewerImage" in controller.data
    assert b"/auto-label" in controller.data


def test_employee_photo_page_contains_export_menu(
    client,
    authenticated_employee,
) -> None:
    """De fotopagina biedt de drie afgesproken exportvormen."""

    page = client.get("/photos/123")
    controller = client.get("/static/js/photo-page-controller.js")
    image_export = client.get("/static/js/viewer/image-export.js")

    assert b'class="photo-export-menu"' in page.data
    assert b'id="export-photo-labels"' in page.data
    assert b'id="export-persons-csv"' in page.data
    assert b'id="export-photo-json"' in page.data
    assert b"exportPhotoWithLabels" in controller.data
    assert b"imageToViewportCoordinates" in image_export.data


def test_information_pages_are_available(client) -> None:
    """Privacy, disclaimer en contact zijn publiek bereikbaar."""

    for path, text in [
        ("/privacy", b"Privacy en persoonsgegevens"),
        ("/disclaimer", b"Disclaimer"),
        ("/contact", b"Contact"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert text in response.data


def test_help_is_context_sensitive(client, authenticated_employee) -> None:
    """De helpinhoud sluit aan op de geopende pagina."""

    overview = client.get("/")
    photo = client.get("/photos/123")
    admin = client.get("/admin")

    assert b"Foto's zoeken en openen" in overview.data
    assert b"De foto bekijken" in photo.data
    assert b"Beheeromgeving" in admin.data
    assert b'id="renumber-person-labels"' in photo.data


def test_photo_label_click_selects_person_for_visitors(client) -> None:
    """Een fotolabel selecteert ook zonder labelbeheer de gekoppelde persoon."""

    javascript = client.get("/static/js/viewer/person-labels.js")

    assert b"createPersonLabelElement(" in javascript.data
    assert b'"pointerdown"' in javascript.data
    assert b"onPersonSelect?.(person.id);" in javascript.data
    assert b"stopViewerInteraction(event);" in javascript.data


def test_admin_import_preview_allows_page_wheel_scrolling(client) -> None:
    """De importvoorvertoning blokkeert de paginascroll niet."""

    css = client.get("/static/css/app.css")

    assert b".admin-workspace .import-results-table" in css.data
    assert b"overscroll-behavior: auto" in css.data


def test_photo_page_uses_clear_label_toolbar_text(
    client, authenticated_employee
) -> None:
    """De labelknoppen gebruiken duidelijke werkwoorden."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b"Label toevoegen" in response.data
    assert b"Hernummeren" in response.data
    assert b">+ Label<" not in response.data
    assert b">Hernummer<" not in response.data


def test_comment_textarea_cannot_be_resized(client) -> None:
    """Het opmerkingenveld heeft geen browser-resizehandvat."""

    css = client.get("/static/css/app.css")

    assert b".comment-textarea" in css.data
    assert b"resize: none" in css.data


def test_photo_page_uses_label_size_slider(client, authenticated_employee) -> None:
    """De labelgrootte gebruikt een slider met min- en plusknop."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="label-size-range"' in response.data
    assert b'id="label-size-decrease"' in response.data
    assert b'id="label-size-increase"' in response.data
    assert b'id="label-size-select"' not in response.data


def test_photo_page_offers_left_to_right_mode(client, authenticated_employee) -> None:
    """Medewerkers kunnen v.l.n.r. als personenweergave kiezen."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="person-display-mode-select"' in response.data
    assert b'value="left_to_right"' in response.data
    assert b">v.l.n.r.<" in response.data


def test_admin_photo_page_offers_delete_from_fno(client, authenticated_admin) -> None:
    """Alleen de beheerpagina bevat de knop Verwijder uit FNO."""

    response = client.get("/photos/123")

    assert response.status_code == 200
    assert b'id="delete-photo-from-fno"' in response.data
    assert b"Verwijder uit FNO" in response.data


def test_visitor_empty_person_layout_is_supported(client) -> None:
    """De frontend kan het personenpaneel voor bezoekers zonder labels verbergen."""

    controller = client.get("/static/js/photo-page-controller.js")
    css = client.get("/static/css/app.css")

    assert b"photo-page--visitor-no-persons" in controller.data
    assert b"photo-page--visitor-no-persons .persons-panel" in css.data
    assert b"photo-page--visitor-no-persons .comments-panel" not in css.data


def test_admin_users_page_is_available(client, authenticated_admin) -> None:
    """Een beheerder kan de gebruikerspagina openen."""

    response = client.get("/admin/users")

    assert response.status_code == 200
    assert b"Gebruikers" in response.data
    assert b"Gebruiker toevoegen" in response.data


def test_employee_cannot_open_admin_users(client, authenticated_employee) -> None:
    """Een medewerker kan gebruikersbeheer niet openen."""

    response = client.get("/admin/users")

    assert response.status_code == 403


def test_authenticated_user_can_open_password_page(
    client, authenticated_employee
) -> None:
    """Een ingelogde gebruiker kan de wachtwoordpagina openen."""

    response = client.get("/account/password")

    assert response.status_code == 200
    assert b"Wachtwoord wijzigen" in response.data
