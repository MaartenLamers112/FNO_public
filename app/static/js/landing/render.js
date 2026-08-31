"use strict";

const COMPARISON_LABELS = Object.freeze({
    green: "Gelijk aan Maior Memorix",
    orange: "Verschilt van Maior Memorix",
    red: "Niet betrouwbaar te vergelijken",
});

const PROGRESS_LABELS = Object.freeze({
    empty: "Nog niets ingevuld",
    partial: "Gedeeltelijk ingevuld",
    complete: "Klaar",
});

export function renderPhotos(container, items, view, options = {}) {
    container.replaceChildren();
    container.className = view === "list" ? "photo-list-view" : `photo-grid photo-grid--${view}`;
    if (items.length === 0) {
        const message = document.createElement("p");
        message.className = "landing-empty-message";
        message.textContent = "Geen foto's gevonden.";
        container.append(message);
        return;
    }
    if (view === "list") container.append(createList(items, options));
    else for (const item of items) container.append(createTile(item, options));
}

export function renderLocationOptions(select, locations, selectedLocation) {
    select.replaceChildren(new Option("Alle plaatsen", ""));
    for (const location of locations) select.append(new Option(location, location));
    select.value = locations.includes(selectedLocation) ? selectedLocation : "";
}

function createTile(photo, options) {
    const tile = document.createElement("article");
    tile.className = "photo-tile";
    const link = createPhotoLink(photo);
    link.className = "photo-tile-main";
    link.append(createThumbnail(photo, "photo-tile-thumbnail"), createPhotoCaption(photo, options));
    tile.append(link);
    return tile;
}

function createList(items, options) {
    const table = document.createElement("table");
    table.className = "photo-list-table";
    const comparisonHeader = options.canViewComparison ? "<th>MM</th>" : "";
    table.innerHTML = `<thead><tr><th>Foto</th><th>Fotonummer</th><th>Onderwerp</th><th>Datering</th><th>Plaats</th><th>Status</th>${comparisonHeader}</tr></thead>`;
    const body = document.createElement("tbody");
    for (const photo of items) {
        const row = document.createElement("tr");
        const thumb = document.createElement("td");
        const link = createPhotoLink(photo);
        link.append(createThumbnail(photo, "photo-list-thumbnail"));
        thumb.append(link);
        const number = document.createElement("td");
        const numberLink = createPhotoLink(photo);
        numberLink.textContent = photo.photo_number;
        number.append(numberLink);
        row.append(
            thumb,
            number,
            textCell(photo.subject),
            textCell(photo.date),
            textCell(photo.location),
            statusCell(photo, options),
        );
        if (options.canViewComparison) row.append(comparisonCell(photo));
        body.append(row);
    }
    table.append(body);
    return table;
}

function createPhotoLink(photo) {
    const link = document.createElement("a");
    link.href = `/photos/${photo.id}`;
    link.dataset.photoLink = "";
    return link;
}

function createThumbnail(photo, className) {
    const wrapper = document.createElement("span");
    wrapper.className = `${className}-wrapper`;
    if (!photo.thumbnail_url) { wrapper.textContent = "Geen miniatuur"; return wrapper; }
    const image = document.createElement("img");
    image.className = className;
    image.src = photo.thumbnail_url;
    image.alt = "";
    image.loading = "lazy";
    wrapper.append(image);
    return wrapper;
}

function createPhotoCaption(photo, options) {
    const caption = document.createElement("span");
    caption.className = "photo-tile-caption";
    const number = document.createElement("span");
    number.textContent = photo.photo_number;
    caption.append(number);
    if (options.canManagePublication) caption.append(createVisibilityToggle(photo));
    caption.append(createStatusDot(photo.progress_status));
    if (options.canViewComparison) caption.append(createComparisonIndicator(photo.comparison));
    return caption;
}

function statusCell(photo, options) {
    const cell = document.createElement("td");
    const wrapper = document.createElement("span");
    wrapper.className = "photo-status-controls";
    if (options.canManagePublication) wrapper.append(createVisibilityToggle(photo));
    else wrapper.append(createVisibilityIcon(photo.is_visible));
    wrapper.append(createStatusDot(photo.progress_status));
    cell.append(wrapper);
    return cell;
}

function createVisibilityToggle(photo) {
    const label = document.createElement("label");
    label.className = "photo-visibility-toggle";
    label.title = visibilityLabel(photo.is_visible);
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = photo.is_visible;
    checkbox.dataset.photoVisibility = "";
    checkbox.dataset.photoId = String(photo.id);
    checkbox.dataset.isComplete = String(photo.is_complete);
    const icon = createVisibilityIcon(photo.is_visible);
    label.append(checkbox, icon);
    checkbox.addEventListener("change", () => {
        updateVisibilityPresentation(label, icon, checkbox.checked);
    });
    return label;
}

function createVisibilityIcon(isVisible) {
    const icon = document.createElement("span");
    icon.className = "photo-visibility-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = visibilityIcon(isVisible);
    return icon;
}

function updateVisibilityPresentation(label, icon, isVisible) {
    icon.textContent = visibilityIcon(isVisible);
    label.title = visibilityLabel(isVisible);
}

function visibilityIcon(isVisible) {
    return isVisible ? "👁" : "◉̸";
}

function visibilityLabel(isVisible) {
    return isVisible
        ? "Zichtbaar voor bezoekers"
        : "Niet zichtbaar voor bezoekers";
}

function createStatusDot(status) {
    const dot = document.createElement("span");
    dot.className = `photo-progress-dot photo-progress-dot--${status}`;
    dot.title = PROGRESS_LABELS[status] ?? status;
    return dot;
}

function comparisonCell(photo) {
    const cell = document.createElement("td");
    cell.append(createComparisonIndicator(photo.comparison));
    return cell;
}

function createComparisonIndicator(comparison) {
    const indicator = document.createElement("span");
    const status = comparison?.status ?? "red";
    indicator.className = `photo-comparison-indicator photo-comparison-indicator--${status}`;
    indicator.textContent = "⇄";
    indicator.title = COMPARISON_LABELS[status] ?? status;
    indicator.setAttribute("aria-label", indicator.title);
    return indicator;
}

function textCell(value) {
    const cell = document.createElement("td");
    cell.textContent = value || "—";
    return cell;
}

