"use strict";

const COMPARISON_LABELS = Object.freeze({
    green: "Gelijk aan Maior Memorix",
    orange: "Verschilt van Maior Memorix",
    red: "Niet betrouwbaar te vergelijken",
});

export function renderPhoto(photo) {
    document.querySelector("#photo-title").textContent = photo.photo_number;
    setValue("#photo-subject", photo.subject);
    setValue("#photo-date", photo.date);
    setValue("#photo-location", photo.location);
    setValue("#photo-description", photo.description);
    resizeDescriptionField();
    renderComparison(photo.comparison);

    const dot = document.querySelector("#photo-progress-dot");
    if (dot) {
        dot.className = `photo-progress-dot photo-progress-dot--${photo.progress_status}`;
        dot.title = progressLabel(photo.progress_status);
        dot.setAttribute("aria-label", dot.title);
    }
    const visible = document.querySelector("#photo-visible");
    if (visible instanceof HTMLInputElement) visible.checked = photo.is_visible;
    const complete = document.querySelector("#photo-complete");
    if (complete instanceof HTMLInputElement) complete.checked = photo.is_complete;
}

export function resizeDescriptionField() {
    const field = document.querySelector("#photo-description");
    if (!(field instanceof HTMLTextAreaElement)) return;

    const computed = window.getComputedStyle(field);
    const lineHeight = Number.parseFloat(computed.lineHeight) || 19.6;
    const verticalChrome =
        Number.parseFloat(computed.paddingTop)
        + Number.parseFloat(computed.paddingBottom)
        + Number.parseFloat(computed.borderTopWidth)
        + Number.parseFloat(computed.borderBottomWidth);
    const page = document.querySelector("#photo-page");
    const maximumLines = page?.classList.contains("photo-page--visitor-no-persons")
        ? 18
        : 6;
    const maximumHeight = (lineHeight * maximumLines) + verticalChrome;

    field.style.height = "auto";
    field.style.height = `${Math.min(field.scrollHeight, maximumHeight)}px`;
    field.style.overflowY = field.scrollHeight > maximumHeight ? "auto" : "hidden";
}

export function renderComparison(comparison) {
    const fields = new Map(
        (comparison?.fields ?? []).map((field) => [field.field, field]),
    );

    for (const indicator of document.querySelectorAll("[data-comparison-field]")) {
        const field = fields.get(indicator.dataset.comparisonField);
        if (!field) {
            indicator.hidden = true;
            continue;
        }

        const status = field.status ?? (field.equal ? "green" : "orange");
        indicator.hidden = false;
        indicator.className = `metadata-comparison metadata-comparison--${status}`;
        indicator.title = comparisonTitle(status, field);
        indicator.setAttribute("aria-label", indicator.title);
    }
}

function comparisonTitle(status, field) {
    const label = COMPARISON_LABELS[status] ?? status;
    if (status === "red") return label;

    const mmValue = field.mm_value || "—";
    const fnoValue = field.fno_value || "—";
    return `${label}\nMM: ${mmValue}\nFNO: ${fnoValue}`;
}

function setValue(selector, value) {
    const field = document.querySelector(selector);
    if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
        field.value = value ?? "";
    }
}

function progressLabel(status) {
    return { empty: "Nog niets ingevuld", partial: "Gedeeltelijk ingevuld", complete: "Klaar" }[status] ?? status;
}
