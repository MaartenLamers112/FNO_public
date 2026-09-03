"use strict";

const SELECTED_CLASS = "person-list-item-selected";

export function renderPersons(
    persons,
    callbacks = {},
    commentCounts = new Map(),
    {
        canContribute = false,
        canManageLabels = false,
        canManageLocks = false,
        canViewComparison = false,
        comparisons = new Map(),
        displayMode = "numbered",
    } = {},
) {
    const list = document.querySelector("#persons-list");
    const empty = document.querySelector("#persons-empty");
    if (!list || !empty) throw new Error("De personenlijst ontbreekt.");

    list.replaceChildren();
    empty.hidden = persons.length !== 0;

    const showNumbers = displayMode === "numbered";
    const panel = document.querySelector(".persons-panel");
    panel?.classList.toggle("persons-panel--without-numbers", !showNumbers);
    const heading = document.querySelector("#persons-number-heading");
    if (heading) heading.textContent = "Nr.";
    const hint = document.querySelector("#persons-display-hint");
    if (hint instanceof HTMLElement) {
        hint.hidden = displayMode !== "left_to_right";
    }

    for (const person of persons) {
        list.append(createPersonListItem(
            person,
            callbacks,
            commentCounts.get(person.id) ?? 0,
            canContribute,
            canManageLabels,
            canManageLocks,
            canViewComparison,
            comparisons.get(person.label_number),
            displayMode,
        ));
    }
}


export function setPersonCommentState(personId, hasComments) {
    const item = document.querySelector(`[data-person-list-id="${personId}"]`);
    const indicator = item?.querySelector(".person-comment-indicator");
    if (!(indicator instanceof HTMLElement)) return false;
    indicator.hidden = !hasComments;
    return true;
}

export function selectPersonInList(personId, { ensureVisible = true } = {}) {
    for (const item of document.querySelectorAll(`.${SELECTED_CLASS}`)) {
        item.classList.remove(SELECTED_CLASS);
        item.removeAttribute("aria-current");
    }

    const item = document.querySelector(`[data-person-list-id="${personId}"]`);
    if (!item) return false;

    item.classList.add(SELECTED_CLASS);
    item.setAttribute("aria-current", "true");
    if (ensureVisible) scrollItemIntoPersonsList(item);
    return true;
}

function createPersonListItem(
    person,
    callbacks,
    commentCount,
    canContribute,
    canManageLabels,
    canManageLocks,
    canViewComparison,
    comparison,
    displayMode,
) {
    const item = document.createElement("li");
    item.className = "person-list-item";
    item.dataset.personListId = String(person.id);

    const numberControl = document.createElement("div");
    numberControl.className = "person-number-control";
    let number = null;
    if (displayMode !== "numbered") {
        numberControl.hidden = true;
    } else {
        number = document.createElement("input");
        number.className = "person-number-input";
        number.type = "text";
        number.inputMode = "numeric";
        number.pattern = "[0-9]*";
        number.value = String(person.label_number);
        number.disabled = !canManageLabels;
        number.setAttribute("aria-label", `Labelnummer ${person.label_number}`);
        numberControl.append(number);
    }

    if (canManageLabels && number) {
        const arrows = document.createElement("span");
        arrows.className = "person-number-arrows";
        arrows.append(
            createNumberArrow("▲", "Naar boven", () => callbacks.onNumberChange?.(person.id, Math.max(1, person.label_number - 1))),
            createNumberArrow("▼", "Naar beneden", () => callbacks.onNumberChange?.(person.id, person.label_number + 1)),
        );
        numberControl.append(arrows);
    }

    const nameWrap = document.createElement("span");
    nameWrap.className = "person-name-wrap";
    const name = document.createElement("input");
    name.className = "person-name-input";
    name.type = "text";
    name.value = person.current_name ?? "";
    name.placeholder = "Naam nog onbekend";
    name.disabled = !canContribute || (person.name_locked && !canManageLocks);
    name.title = person.name_locked ? "Naam is vergrendeld" : "";
    name.setAttribute("aria-label", `Naam bij label ${person.label_number}`);
    const commentIndicator = document.createElement("span");
    commentIndicator.className = "person-comment-indicator";
    commentIndicator.hidden = commentCount === 0;
    commentIndicator.title = `${commentCount} opmerking(en) aanwezig`;
    commentIndicator.setAttribute("aria-label", "Opmerking aanwezig");
    nameWrap.append(name, commentIndicator);
    if (canViewComparison) {
        nameWrap.append(createPersonComparisonIndicator(person, comparison));
    }

    item.addEventListener("click", () => callbacks.onPersonSelect?.(person.id));
    number?.addEventListener("click", (event) => { event.stopPropagation(); callbacks.onPersonInputSelect?.(person.id); });
    number?.addEventListener("change", () => callbacks.onNumberChange?.(person.id, Number(number.value)));
    number?.addEventListener("keydown", (event) => { if (event.key === "Enter") number.blur(); });
    name.addEventListener("click", (event) => { event.stopPropagation(); callbacks.onPersonInputSelect?.(person.id); });
    name.addEventListener("change", () => callbacks.onNameChange?.(person.id, name.value));
    name.addEventListener("keydown", (event) => {
        if (event.key === "Enter") { event.preventDefault(); void callbacks.onNameEnter?.(person.id, name.value); }
        if (event.key === "Escape") name.blur();
    });

    if (canManageLocks) {
        const lock = document.createElement("button");
        lock.type = "button";
        lock.className = "person-lock-button";
        lock.textContent = person.name_locked ? "🔒" : "🔓";
        lock.title = person.name_locked ? "Naam ontgrendelen" : "Naam vergrendelen";
        lock.addEventListener("click", (event) => { event.stopPropagation(); callbacks.onLockChange?.(person.id, !person.name_locked); });
        item.append(numberControl, nameWrap, lock);
    } else {
        item.append(numberControl, nameWrap);
    }
    return item;
}


function createPersonComparisonIndicator(person, comparison) {
    const indicator = document.createElement("span");
    const status = comparison?.status ?? "red";
    indicator.className = `person-comparison person-comparison--${status}`;
    indicator.textContent = "⇄";
    const label = {
        green: "Gelijk aan Maior Memorix",
        orange: "Verschilt van Maior Memorix",
        red: "Niet betrouwbaar te vergelijken",
    }[status] ?? status;
    const mmName = comparison?.mm_name || "—";
    const fnoName = comparison?.fno_name || person.current_name || "—";
    indicator.title = status === "red"
        ? label
        : `${label}\nMM: ${mmName}\nFNO: ${fnoName}`;
    indicator.setAttribute("aria-label", indicator.title);
    return indicator;
}

function createNumberArrow(symbol, label, callback) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "person-number-arrow";
    button.textContent = symbol;
    button.setAttribute("aria-label", label);
    button.addEventListener("click", (event) => {
        event.stopPropagation();
        callback();
    });
    return button;
}

function scrollItemIntoPersonsList(item) {
    const list = document.querySelector("#persons-list");
    if (!list) return;

    const itemRect = item.getBoundingClientRect();
    const listRect = list.getBoundingClientRect();
    if (itemRect.top < listRect.top) {
        list.scrollBy({ top: itemRect.top - listRect.top, behavior: "smooth" });
    }
    if (itemRect.bottom > listRect.bottom) {
        list.scrollBy({ top: itemRect.bottom - listRect.bottom, behavior: "smooth" });
    }
}


export function focusPersonName(personId) {
    const item = document.querySelector(`[data-person-list-id="${personId}"]`);
    const input = item?.querySelector(".person-name-input");
    if (!(input instanceof HTMLInputElement)) return false;
    input.focus({ preventScroll: true });
    input.select();
    return true;
}
