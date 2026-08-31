"use strict";

const FILTER_STORAGE_KEY = "fno.mmImport.filters";

function normalize(value) {
    return (value ?? "").trim().toLocaleLowerCase("nl-NL");
}

function datasetKey(field) {
    return field.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

function getFilterControls(form) {
    return [...form.querySelectorAll("select[name], input[name]")].filter(
        (control) => control.name !== "csrf_token",
    );
}

function restoreImportFilters(form) {
    const controls = getFilterControls(form);
    let stored = {};

    try {
        stored = JSON.parse(sessionStorage.getItem(FILTER_STORAGE_KEY) ?? "{}");
    } catch {
        stored = {};
    }

    const saveFilters = () => {
        const values = Object.fromEntries(
            controls.map((control) => [control.name, control.value]),
        );
        sessionStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(values));
    };

    for (const control of controls) {
        if (!control.value && typeof stored[control.name] === "string") {
            control.value = stored[control.name];
        }
        control.addEventListener("change", saveFilters);
        control.addEventListener("input", saveFilters);
    }

    form.addEventListener("submit", saveFilters);

    const hasPreview = Boolean(document.querySelector("[data-import-preview]"));
    const hasStoredFilter = Object.values(stored).some((value) => value);
    if (!hasPreview && hasStoredFilter) {
        const action = document.createElement("input");
        action.type = "hidden";
        action.name = "action";
        action.value = "preview";
        form.append(action);
        form.requestSubmit();
    }
}

class ImportPreviewController {
    constructor(preview) {
        this.preview = preview;
        this.rows = [...preview.querySelectorAll("[data-import-record]")];
        this.filters = [...preview.querySelectorAll("[data-column-filter]")];
        this.elements = {
            visibleCount: preview.querySelector("[data-visible-count]"),
            selectedCount: preview.querySelector("[data-selected-count]"),
            selectedCountSummary: preview.querySelector("[data-selected-count-summary]"),
            importCount: preview.querySelector("[data-import-count]"),
            importButton: preview.querySelector("[data-import-button]"),
            selectVisibleButton: preview.querySelector("[data-select-visible]"),
            clearSelectionButton: preview.querySelector("[data-clear-selection]"),
            toggleVisible: preview.querySelector("[data-toggle-visible]"),
        };
    }

    initialize() {
        this.#addSortButtons();
        this.#populateFilterOptions();
        this.#bindEvents();
        this.#applyFilters();
    }

    #addSortButtons() {
        const sortableFields = [
            null,
            null,
            "photo-number",
            "title",
            "date",
            "location",
            "subject",
            "collection-part",
            "status",
        ];
        const headerCells = [
            ...this.preview.querySelectorAll(".import-column-labels th"),
        ];

        headerCells.forEach((cell, index) => {
            const field = sortableFields[index];
            if (!field) return;

            const button = document.createElement("button");
            button.type = "button";
            button.className = "import-sort-button";
            button.textContent = "↕";
            button.title = "Sorteer deze kolom";
            let direction = 1;

            button.addEventListener("click", () => {
                this.#sortRows(field, direction);
                direction *= -1;
                button.textContent = direction === -1 ? "↑" : "↓";
            });
            cell.append(button);
        });
    }

    #sortRows(field, direction) {
        this.rows.sort((left, right) => direction * this.#sortValue(
            left,
            field,
        ).localeCompare(
            this.#sortValue(right, field),
            "nl-NL",
            { numeric: true },
        ));

        const body = this.rows[0]?.parentElement;
        if (body) {
            this.rows.forEach((row) => body.append(row));
        }
    }

    #sortValue(row, field) {
        return normalize(row.dataset[datasetKey(field)]);
    }

    #populateFilterOptions() {
        for (const filter of this.filters) {
            if (
                filter instanceof HTMLSelectElement
                && filter.dataset.columnFilter !== "status"
            ) {
                this.#addSelectOptions(filter, datasetKey(filter.dataset.columnFilter));
            }
        }
    }

    #addSelectOptions(select, field) {
        const values = new Set();
        for (const row of this.rows) {
            const value = row.dataset[field];
            if (value) values.add(value);
        }

        const sorted = [...values].sort((left, right) => left.localeCompare(
            right,
            "nl-NL",
        ));
        for (const value of sorted) {
            select.append(new Option(value, value));
        }
    }

    #bindEvents() {
        for (const filter of this.filters) {
            filter.addEventListener(
                filter instanceof HTMLInputElement ? "input" : "change",
                () => this.#applyFilters(),
            );
        }

        this.rows.forEach((row) => {
            this.#checkboxFor(row)?.addEventListener(
                "change",
                () => this.#updateCounters(),
            );
        });

        this.elements.selectVisibleButton?.addEventListener(
            "click",
            () => this.#setVisibleSelection(true),
        );
        this.elements.clearSelectionButton?.addEventListener(
            "click",
            () => this.#clearSelection(),
        );
        this.elements.toggleVisible?.addEventListener("change", () => {
            this.#setVisibleSelection(this.elements.toggleVisible.checked);
        });
    }

    #applyFilters() {
        for (const row of this.rows) {
            row.hidden = !this.filters.every((filter) => this.#matchesFilter(
                row,
                filter,
            ));
        }
        this.#updateCounters();
    }

    #matchesFilter(row, filter) {
        const expected = normalize(filter.value);
        if (!expected) return true;

        const actual = normalize(
            row.dataset[datasetKey(filter.dataset.columnFilter)],
        );
        return filter instanceof HTMLInputElement
            ? actual.includes(expected)
            : actual === expected;
    }

    #setVisibleSelection(selected) {
        for (const row of this.#visibleRows()) {
            const checkbox = this.#checkboxFor(row);
            if (checkbox && !checkbox.disabled) checkbox.checked = selected;
        }
        this.#updateCounters();
    }

    #clearSelection() {
        for (const row of this.rows) {
            const checkbox = this.#checkboxFor(row);
            if (checkbox && !checkbox.disabled) checkbox.checked = false;
        }
        this.#updateCounters();
    }

    #updateCounters() {
        const selected = this.rows.filter(
            (row) => this.#checkboxFor(row)?.checked,
        ).length;
        const selectableVisible = this.#visibleRows().filter(
            (row) => !this.#checkboxFor(row)?.disabled,
        );
        const allVisibleSelected = selectableVisible.length > 0
            && selectableVisible.every((row) => this.#checkboxFor(row)?.checked);
        const someVisibleSelected = selectableVisible.some(
            (row) => this.#checkboxFor(row)?.checked,
        );

        this.#setText(this.elements.visibleCount, this.#visibleRows().length);
        this.#setText(this.elements.selectedCount, selected);
        this.#setText(this.elements.selectedCountSummary, selected);
        this.#setText(this.elements.importCount, selected);
        if (this.elements.importButton) {
            this.elements.importButton.disabled = selected === 0;
        }
        if (this.elements.toggleVisible instanceof HTMLInputElement) {
            this.elements.toggleVisible.checked = allVisibleSelected;
            this.elements.toggleVisible.indeterminate = !allVisibleSelected
                && someVisibleSelected;
        }
    }

    #setText(element, value) {
        if (element) element.textContent = String(value);
    }

    #visibleRows() {
        return this.rows.filter((row) => !row.hidden);
    }

    #checkboxFor(row) {
        return row.querySelector("[data-record-checkbox]");
    }
}

const filterForm = document.querySelector("[data-import-filter-form]");
if (filterForm instanceof HTMLFormElement) {
    restoreImportFilters(filterForm);
}

const preview = document.querySelector("[data-import-preview]");
if (preview instanceof HTMLElement) {
    new ImportPreviewController(preview).initialize();
}
