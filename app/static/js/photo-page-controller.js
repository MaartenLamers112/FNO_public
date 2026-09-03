"use strict";

import { get, patch, post, postForm, remove } from "./api.js";
import {
    focusPersonName,
    renderPersons,
    selectPersonInList,
    setPersonCommentState,
} from "./persons.js";
import { renderPhoto, resizeDescriptionField } from "./photo-details.js";
import { DragManager } from "./viewer/drag-manager.js";
import { captureViewerImage } from "./viewer/image-capture.js";
import { exportPhotoWithLabels } from "./viewer/image-export.js";
import { initializeViewer } from "./viewer/index.js";
import { LabelPlacementManager } from "./viewer/label-placement-manager.js";
import { renderPersonLabels, selectPersonLabel } from "./viewer/person-labels.js";
import { contextNeighbours, rememberPhoto } from "./navigation-context.js";

export class PhotoPageController {
    constructor(page) {
        if (!(page instanceof HTMLElement)) throw new Error("Ongeldige fotopagina.");
        this.page = page;
        this.photoId = page.dataset.photoId;
        this.canContribute = page.dataset.canContribute === "true";
        this.canManageLabels = page.dataset.canManageLabels === "true";
        this.canManagePublication = page.dataset.canManagePublication === "true";
        this.canViewComparison = page.dataset.canViewComparison === "true";
        this.persons = [];
        this.photoComparison = null;
        this.photoNumber = "foto";
        this.personDisplayMode = "numbered";
        this.personDisplayCount = 1;
        this.labelSize = 14;
        this.commentCounts = new Map();
        this.selectedPersonId = null;
        this.viewer = null;
        this.overlayManager = null;
        this.dragManager = null;
        this.labelPlacementManager = null;
        this.commentSaveTimer = null;
        this.loadedCommentText = "";
    }

    async initialize() {
        const photo = await get(`/api/photos/${this.photoId}`);
        const [persons, comments] = await Promise.all([
            get(`/api/photos/${this.photoId}/persons`),
            get(`/api/photos/${this.photoId}/comments`),
        ]);
        rememberPhoto(this.photoId);
        this.photoComparison = photo.comparison ?? null;
        this.photoNumber = photo.photo_number;
        this.personDisplayMode = photo.person_display_mode ?? "numbered";
        this.personDisplayCount = photo.person_display_count ?? 1;
        this.labelSize = photo.label_size ?? 14;
        this.persons = persons;
        this.#setCommentCounts(comments);
        renderPhoto(photo);
        this.#updatePhotoNavigation(photo);
        this.#renderPersons();
        this.#showContent();
        await new Promise((resolve) => window.requestAnimationFrame(resolve));

        const context = initializeViewer({
            elementId: "photo-viewer",
            imageSource: photo.image_source,
            prefixUrl: this.page.dataset.viewerPrefixUrl,
        });
        this.viewer = context.viewer;
        this.overlayManager = context.overlayManager;
        if (this.canManageLabels) {
            this.dragManager = new DragManager(this.viewer, this.overlayManager);
            this.labelPlacementManager = new LabelPlacementManager(
                this.viewer,
                (position) => void this.#createPerson(position),
            );
        }
        this.#bindControls();
        this.#initializeLabelSize();
        this.#renderPersonLabels();
    }

    #updatePhotoNavigation(photo) {
        const neighbours = contextNeighbours(this.photoId);
        this.#setPhotoNavigationLink(
            "#previous-photo-link",
            neighbours ? neighbours.previousPhotoId : photo.previous_photo_id,
        );
        this.#setPhotoNavigationLink(
            "#next-photo-link",
            neighbours ? neighbours.nextPhotoId : photo.next_photo_id,
        );
    }

    #setPhotoNavigationLink(selector, photoId) {
        const link = document.querySelector(selector);
        if (!(link instanceof HTMLAnchorElement)) return;

        if (photoId === null || photoId === undefined) {
            link.hidden = true;
            link.removeAttribute("href");
            return;
        }

        link.href = `/photos/${photoId}`;
        link.hidden = false;
    }

    #renderPersons() {
        const persons = this.#displayPersons();
        renderPersons(
            persons,
            {
                onPersonSelect: (id) => void this.#openComments(id, { focusInput: false }),
                onPersonInputSelect: (id) => void this.#openComments(
                    id,
                    { focusInput: false },
                ),
                onNameChange: (id, name) => void this.#changeName(id, name),
                onNameEnter: (id, name) => void this.#saveNameAndFocusNext(id, name),
                onNumberChange: (id, number) => void this.#changeNumber(id, number),
                onCommentsOpen: (id) => void this.#openComments(id),
                onLockChange: (id, locked) => void this.#changeNameLock(id, locked),
            },
            this.commentCounts,
            {
                canContribute: this.canContribute,
                canManageLabels: this.canManageLabels,
                canManageLocks: this.canManagePublication,
                canViewComparison: this.canViewComparison,
                comparisons: this.#personComparisons(),
                displayMode: this.personDisplayMode,
            },
        );
        this.#updateVisitorPersonLayout();
    }

    #renderPersonLabels() {
        renderPersonLabels({
            persons: this.persons,
            viewer: this.viewer,
            overlayManager: this.overlayManager,
            dragManager: this.dragManager,
            onPersonSelect: (id) => void this.#openComments(id, { focusInput: false }),
            onPersonMove: (position) => void this.#movePerson(position),
            displayMode: this.personDisplayMode,
            showInternalNumbers: this.canManageLabels && this.personDisplayMode === "numbered",
        });
    }

    #bindMetadataControls() {
        const fields = [
            "#photo-subject",
            "#photo-date",
            "#photo-location",
            "#photo-description",
        ];
        for (const selector of fields) {
            const field = document.querySelector(selector);
            field?.addEventListener("change", () => void this.#saveMetadata());
        }
        document.querySelector("#photo-description")?.addEventListener(
            "input",
            resizeDescriptionField,
        );
        const visible = document.querySelector("#photo-visible");
        const complete = document.querySelector("#photo-complete");
        if (this.canManagePublication) {
            visible?.addEventListener("change", () => void this.#saveManagement());
            complete?.addEventListener("change", () => void this.#saveManagement());
        }
    }

    async #saveMetadata() {
        await this.#runAction("Metadata opslaan…", async () => {
            await patch(
                `/api/photos/${this.photoId}/metadata`,
                this.#metadataValues(),
            );
            await this.#reloadComparison();
        });
    }

    async #saveManagement() {
        await this.#runAction("Beheerstatus opslaan…", async () => {
            const photo = await patch(`/api/photos/${this.photoId}/management`, {
                is_visible: Boolean(document.querySelector("#photo-visible")?.checked),
                is_complete: Boolean(document.querySelector("#photo-complete")?.checked),
            });
            renderPhoto({ ...photo, ...this.#metadataValues() });
        });
    }

    #metadataValues() {
        return {
            subject: this.#fieldValue("#photo-subject"),
            date: this.#fieldValue("#photo-date"),
            location: this.#fieldValue("#photo-location"),
            description: this.#fieldValue("#photo-description"),
        };
    }

    #fieldValue(selector) {
        const field = document.querySelector(selector);
        return field instanceof HTMLInputElement
            || field instanceof HTMLTextAreaElement
            ? field.value
            : "";
    }

    #bindControls() {
        this.#bindMetadataControls();
        const placement = document.querySelector("#toggle-label-placement");
        const removeButton = document.querySelector("#delete-person-label");
        const commentInput = document.querySelector("#comment-content");
        if (!(commentInput instanceof HTMLTextAreaElement)) {
            throw new Error("Bediening ontbreekt.");
        }

        placement?.addEventListener("click", () => {
            const enabled = placement.getAttribute("aria-pressed") !== "true";
            this.#setPlacementEnabled(enabled);
        });
        removeButton?.addEventListener("click", () => void this.#deleteSelectedPerson());
        document.querySelector("#delete-all-person-labels")?.addEventListener(
            "click",
            () => void this.#deleteAllPersons(),
        );
        document.querySelector("#detect-persons")?.addEventListener(
            "click",
            () => void this.#detectPersons(),
        );
        document.querySelector("#renumber-person-labels")?.addEventListener(
            "click",
            () => void this.#renumberPersons(),
        );
        document.querySelector("#export-photo-labels")?.addEventListener(
            "click",
            () => void this.#exportPhotoWithLabels(),
        );
        this.#configureExportLinks();
        document.querySelector("#person-display-mode-select")?.addEventListener(
            "change",
            (event) => void this.#setPersonDisplayMode(event.target.value),
        );
        document.querySelector("#person-display-count-select")?.addEventListener(
            "change",
            (event) => void this.#setPersonDisplayCount(event.target.value),
        );
        document.querySelector("#label-size-range")?.addEventListener(
            "input",
            (event) => this.#setLabelSize(event.target.value),
        );
        document.querySelector("#label-size-range")?.addEventListener(
            "change",
            () => void this.#saveLabelSize(),
        );
        document.querySelector("#label-size-decrease")?.addEventListener(
            "click",
            () => void this.#adjustLabelSize(-1),
        );
        document.querySelector("#label-size-increase")?.addEventListener(
            "click",
            () => void this.#adjustLabelSize(1),
        );
        document.querySelector("#label-size-value")?.addEventListener(
            "input",
            (event) => this.#previewLabelSizeValue(event.target.value),
        );
        document.querySelector("#label-size-value")?.addEventListener(
            "change",
            () => void this.#saveLabelSize(),
        );
        document.querySelector("#delete-photo-from-fno")?.addEventListener(
            "click",
            () => void this.#deletePhotoFromFno(),
        );
        commentInput.addEventListener("input", () => this.#scheduleCommentSave());
        commentInput.addEventListener("blur", () => void this.#saveCommentText());
        window.addEventListener("keydown", (event) => this.#handleKeyboard(event), { capture: true });
        document.querySelector("#dismiss-error-message")?.addEventListener(
            "click",
            () => this.#hideError(),
        );
        this.#updateActions();
    }

    #configureExportLinks() {
        const textLink = document.querySelector("#export-photo-text");
        const csvLink = document.querySelector("#export-persons-csv");
        const jsonLink = document.querySelector("#export-photo-json");
        if (textLink instanceof HTMLAnchorElement) {
            textLink.href = `/api/photos/${this.photoId}/export.txt`;
        }
        if (csvLink instanceof HTMLAnchorElement) {
            csvLink.href = `/api/photos/${this.photoId}/export.csv`;
        }
        if (jsonLink instanceof HTMLAnchorElement) {
            jsonLink.href = `/api/photos/${this.photoId}/export.json`;
        }
    }

    async #exportPhotoWithLabels() {
        await this.#runAction("Foto exporteren…", async () => {
            await exportPhotoWithLabels({
                viewer: this.viewer,
                persons: this.persons,
                photoNumber: this.photoNumber,
                labelFontSize: this.labelSize,
                showLabels: this.personDisplayMode === "numbered",
            });
        });
    }

    async #renumberPersons() {
        if (!this.persons.length) {
            window.alert("Er zijn geen labels om te hernummeren.");
            return;
        }
        if (!window.confirm(
            "Labels opnieuw nummeren van boven naar beneden en per rij van links naar rechts?",
        )) return;

        await this.#runAction("Labels hernummeren…", async () => {
            this.persons = await post(
                `/api/photos/${this.photoId}/persons/renumber`,
                {},
            );
            this.persons.sort((a, b) => a.label_number - b.label_number);
            this.#renderPersons();
            this.#renderPersonLabels();
            await this.#reloadComparison();
        });
    }

    async #detectPersons() {
        this.#setPlacementEnabled(false);
        const button = document.querySelector("#detect-persons");
        if (button instanceof HTMLButtonElement) {
            button.disabled = true;
            button.textContent = "Auto labelen…";
        }

        try {
            await this.#runAction("Auto labelen…", async () => {
                const image = await captureViewerImage(this.viewer);
                const formData = new FormData();
                formData.append("image", image, `photo-${this.photoId}.jpg`);

                const result = await postForm(
                    `/api/photos/${this.photoId}/auto-label`,
                    formData,
                );
                this.persons = result.persons;
                this.persons.sort((a, b) => a.label_number - b.label_number);
                this.#renderPersons();
                this.#renderPersonLabels();
                await this.#reloadComparison();

                if (!result.created_count) {
                    window.alert(
                        result.skipped_existing_count
                            ? "Geen nieuwe personen gevonden naast de bestaande labels."
                            : "Geen personen gevonden. Voeg ontbrekende labels handmatig toe.",
                    );
                    return;
                }
                window.alert(`${result.created_count} label(s) automatisch toegevoegd.`);
            });
        } finally {
            if (button instanceof HTMLButtonElement) {
                button.disabled = false;
                button.textContent = "Auto label";
            }
        }
    }

    async #createPerson({ xPosition, yPosition }) {
        await this.#runAction("Label toevoegen…", async () => {
            const person = await post(`/api/photos/${this.photoId}/persons`, {
                x_position: xPosition,
                y_position: yPosition,
            });
            this.persons.push(person);
            this.persons.sort((a, b) => a.label_number - b.label_number);
            await this.#reloadComparison();
            this.#renderPersons();
            this.#renderPersonLabels();
            await this.#openComments(person.id, { focusInput: false });
        });
    }

    async #changeName(personId, currentName) {
        await this.#runAction("Naam opslaan…", async () => {
            const updated = await patch(`/api/persons/${personId}/name`, {
                current_name: currentName,
            });
            this.#replacePerson(updated);
            await this.#reloadComparison();
            this.#renderPersons();
            this.#renderPersonLabels();
            this.#selectPerson(personId, { ensureVisible: false });
        });
    }

    async #changeNameLock(personId, nameLocked) {
        await this.#runAction("Naamvergrendeling opslaan…", async () => {
            const existing = this.persons.find((person) => person.id === personId);
            const updated = await patch(`/api/persons/${personId}/name-lock`, {
                name_locked: nameLocked,
            });
            if ((updated.current_name === null || updated.current_name === undefined) && existing) {
                updated.current_name = existing.current_name;
            }
            this.#replacePerson(updated);
            this.#renderPersons();
            this.#selectPerson(personId, { ensureVisible: false });
        });
    }

    async #saveNameAndFocusNext(personId, currentName) {
        await this.#changeName(personId, currentName);
        const persons = this.#displayPersons();
        const index = persons.findIndex((person) => person.id === personId);
        const next = persons[index + 1];
        if (!next) return;
        await this.#openComments(next.id, { focusInput: false });
        focusPersonName(next.id);
    }

    async #changeNumber(personId, labelNumber) {
        await this.#runAction("Nummer wijzigen…", async () => {
            await patch(`/api/persons/${personId}/number`, { label_number: labelNumber });
            await this.#reloadPersons();
            await this.#reloadComparison();
            this.#selectPerson(personId);
        });
    }

    async #movePerson({ personId, xPosition, yPosition }) {
        await this.#runAction("Positie opslaan…", async () => {
            const updated = await patch(
                `/api/persons/${personId}/position`,
                { x_position: xPosition, y_position: yPosition },
            );
            this.#replacePerson(updated);
            this.#renderPersons();
            this.#renderPersonLabels();
            this.#selectPerson(personId, { ensureVisible: false });
        });
    }

    #initializeLabelSize() {
        this.#setLabelSize(this.labelSize);
        const displayMode = document.querySelector("#person-display-mode-select");
        if (displayMode instanceof HTMLSelectElement) {
            displayMode.value = this.personDisplayMode;
        }
        this.#updatePersonDisplayControls();
    }

    #setLabelSize(size) {
        const parsed = Number.parseInt(size, 10);
        const candidate = Number.isInteger(parsed) ? parsed : this.labelSize;
        const normalized = Math.min(Math.max(candidate, 5), 30);
        this.labelSize = normalized;
        this.page.style.setProperty("--person-label-font-size", `${normalized}px`);
        const range = document.querySelector("#label-size-range");
        if (range instanceof HTMLInputElement) range.value = String(normalized);
        const valueInput = document.querySelector("#label-size-value");
        if (valueInput instanceof HTMLInputElement) {
            valueInput.value = String(normalized);
        }
    }

    #previewLabelSizeValue(value) {
        const parsed = Number.parseInt(value, 10);
        if (!Number.isInteger(parsed)) return;
        this.#setLabelSize(parsed);
    }

    async #adjustLabelSize(delta) {
        const next = Math.min(Math.max(this.labelSize + delta, 5), 30);
        this.#setLabelSize(next);
        await this.#saveLabelSize();
    }

    async #saveLabelSize() {
        await this.#runAction("Labelgrootte opslaan…", async () => {
            const response = await patch(
                `/api/photos/${this.photoId}/label-size`,
                { label_size: this.labelSize },
            );
            this.#setLabelSize(response.label_size);
        });
    }

    async #setPersonDisplayMode(mode) {
        let targetCount = this.personDisplayCount;
        if (mode === "single_person") targetCount = 1;
        if (mode === "left_to_right") {
            targetCount = Math.max(2, targetCount, this.persons.length);
        }
        if (targetCount < this.persons.length && !window.confirm(
            `Het aantal personen wordt verlaagd naar ${targetCount}. `
            + "De laatste naamregels en gekoppelde opmerkingen worden verwijderd. Doorgaan?",
        )) {
            const select = document.querySelector("#person-display-mode-select");
            if (select instanceof HTMLSelectElement) select.value = this.personDisplayMode;
            return;
        }
        await this.#savePersonDisplay(mode, targetCount);
    }

    async #setPersonDisplayCount(value) {
        const targetCount = Number.parseInt(value, 10);
        if (!Number.isInteger(targetCount)) return;
        if (targetCount < this.persons.length && !window.confirm(
            `Het aantal personen wordt verlaagd naar ${targetCount}. `
            + "De laatste naamregels en gekoppelde opmerkingen worden verwijderd. Doorgaan?",
        )) {
            this.#updatePersonDisplayControls();
            return;
        }
        await this.#savePersonDisplay("left_to_right", targetCount);
    }

    async #savePersonDisplay(mode, count) {
        await this.#runAction("Personenweergave opslaan…", async () => {
            const response = await patch(
                `/api/photos/${this.photoId}/person-display-mode`,
                {
                    person_display_mode: mode,
                    person_display_count: count,
                },
            );
            this.personDisplayMode = response.person_display_mode;
            this.personDisplayCount = response.person_display_count;
            await this.#reloadPersons();
            this.#updatePersonDisplayControls();
            this.#renderPersons();
            this.#renderPersonLabels();
        });
    }

    #updatePersonDisplayControls() {
        const countControl = document.querySelector("#person-display-count-control");
        if (countControl instanceof HTMLElement) {
            countControl.hidden = this.personDisplayMode !== "left_to_right";
        }
        const countSelect = document.querySelector("#person-display-count-select");
        if (countSelect instanceof HTMLSelectElement) {
            countSelect.value = String(Math.max(2, this.personDisplayCount));
        }
    }

    async #deletePhotoFromFno() {
        if (!this.canManagePublication) return;
        const confirmed = window.confirm(
            "Deze foto uit FNO verwijderen?\n\n"
            + "Alle FNO-labels, namen, opmerkingen en historie van deze foto worden verwijderd. "
            + "Maior Memorix wordt niet gewijzigd.",
        );
        if (!confirmed) return;

        await this.#runAction("Foto verwijderen…", async () => {
            await remove(`/api/photos/${this.photoId}`);
            window.location.assign("/");
        });
    }

    #displayPersons() {
        if (this.personDisplayMode !== "left_to_right") return this.persons;
        return [...this.persons].sort(
            (left, right) => left.x_position - right.x_position
                || left.y_position - right.y_position,
        );
    }

    #updateVisitorPersonLayout() {
        const hidePersonPanels = !this.canManageLabels && this.persons.length === 0;
        this.page.classList.toggle("photo-page--visitor-no-persons", hidePersonPanels);
        resizeDescriptionField();
    }

    async #deleteAllPersons() {
        if (!this.persons.length) return;
        const confirmed = window.confirm(
            `Alle ${this.persons.length} labels van deze foto verwijderen?\n\n`
            + "Namen en opmerkingen die aan deze labels zijn gekoppeld worden ook verwijderd. "
            + "De wijziging blijft in de historie zichtbaar.",
        );
        if (!confirmed) return;

        await this.#runAction("Alle labels verwijderen…", async () => {
            await remove(`/api/photos/${this.photoId}/persons`);
            this.persons = [];
            this.selectedPersonId = null;
            await this.#reloadComparison();
            this.#renderPersons();
            this.#renderPersonLabels();
            await this.#openComments(null);
        });
    }

    async #deleteSelectedPerson() {
        const person = this.#selectedPerson();
        if (!person || !window.confirm(`Label ${person.label_number} verwijderen?`)) return;
        await this.#runAction("Label verwijderen…", async () => {
            await remove(`/api/persons/${person.id}`);
            this.selectedPersonId = null;
            await this.#reloadPersons();
            await this.#reloadComparison();
            await this.#openComments(null);
        });
    }

    async #openComments(personId, { focusInput = true } = {}) {
        window.clearTimeout(this.commentSaveTimer);
        this.commentSaveTimer = null;
        this.selectedPersonId = personId;
        this.#updateActions();

        const title = document.querySelector("#comments-title");
        const input = document.querySelector("#comment-content");
        if (!title || !(input instanceof HTMLTextAreaElement)) return;

        if (personId === null) {
            title.textContent = "Opmerkingen";
            input.value = "";
            input.disabled = true;
            this.loadedCommentText = "";
            return;
        }

        this.#selectPerson(personId);
        const person = this.#selectedPerson();
        title.textContent = this.personDisplayMode === "numbered"
            ? `Opmerkingen bij ${person.label_number}`
            : "Opmerkingen bij geselecteerde persoon";
        input.disabled = true;
        input.value = "";
        this.loadedCommentText = "";
        const comments = await get(`/api/persons/${personId}/comments`);
        if (this.selectedPersonId !== personId) return;
        const content = comments.map((comment) => comment.content).join("\n\n");
        const hasComments = Boolean(content.trim());
        this.commentCounts.set(personId, hasComments ? 1 : 0);
        setPersonCommentState(personId, hasComments);
        this.#selectPerson(personId, { ensureVisible: false });
        input.disabled = false;
        input.value = content;
        this.loadedCommentText = content.trim();
        if (focusInput) {
            input.focus({ preventScroll: true });
            input.setSelectionRange(input.value.length, input.value.length);
        }
    }

    #scheduleCommentSave() {
        window.clearTimeout(this.commentSaveTimer);
        this.commentSaveTimer = window.setTimeout(
            () => void this.#saveCommentText(),
            700,
        );
    }

    async #saveCommentText() {
        window.clearTimeout(this.commentSaveTimer);
        this.commentSaveTimer = null;

        const person = this.#selectedPerson();
        const input = document.querySelector("#comment-content");
        if (!person || !(input instanceof HTMLTextAreaElement)) return;

        const content = input.value.trim();
        if (content === this.loadedCommentText) return;

        await this.#runAction("Opmerking opslaan…", async () => {
            const response = await patch(`/api/persons/${person.id}/comments-text`, {
                content: input.value,
            });
            this.loadedCommentText = response.content;
            this.commentCounts.set(person.id, response.has_comment ? 1 : 0);
            setPersonCommentState(person.id, response.has_comment);
            this.#selectPerson(person.id, { ensureVisible: false });
        });
    }

    #selectPerson(personId, { ensureVisible = true } = {}) {
        this.selectedPersonId = personId;
        selectPersonInList(personId, { ensureVisible });
        selectPersonLabel({ personId, overlayManager: this.overlayManager });
        this.#updateActions();
    }

    #handleKeyboard(event) {
        if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;

        if (event.key === "Escape") {
            this.#setPlacementEnabled(false);
            return;
        }
        if (this.canManageLabels && event.key.toLowerCase() === "n") {
            event.preventDefault();
            const placement = document.querySelector("#toggle-label-placement");
            const enabled = placement?.getAttribute("aria-pressed") !== "true";
            this.#setPlacementEnabled(enabled);
            return;
        }
        if (this.canManageLabels && (event.key === "Delete" || event.code === "Delete" || event.keyCode === 46)) {
            event.preventDefault();
            void this.#deleteSelectedPerson();
        }
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            event.preventDefault();
            const persons = this.#displayPersons();
            const index = persons.findIndex((person) => person.id === this.selectedPersonId);
            const delta = event.key === "ArrowDown" ? 1 : -1;
            const next = Math.min(Math.max(index + delta, 0), persons.length - 1);
            if (persons[next]) {
                void this.#openComments(persons[next].id, { focusInput: false });
            }
        }
    }

    #setPlacementEnabled(enabled) {
        const placement = document.querySelector("#toggle-label-placement");
        if (!(placement instanceof HTMLButtonElement) || !this.labelPlacementManager) return;
        placement.setAttribute("aria-pressed", String(enabled));
        placement.textContent = enabled ? "Plaatsen stoppen" : "Label toevoegen";
        this.labelPlacementManager.setEnabled(enabled);
    }

    async #reloadPersons() {
        this.persons = await get(`/api/photos/${this.photoId}/persons`);
        this.#renderPersons();
        this.#renderPersonLabels();
        this.#updateActions();
    }

    async #reloadComparison() {
        if (!this.canViewComparison) return;
        const photo = await get(`/api/photos/${this.photoId}`);
        rememberPhoto(this.photoId);
        this.photoComparison = photo.comparison ?? null;
        this.photoNumber = photo.photo_number;
        this.personDisplayMode = photo.person_display_mode ?? this.personDisplayMode;
        this.personDisplayCount = photo.person_display_count ?? this.personDisplayCount;
        this.labelSize = photo.label_size ?? this.labelSize;
        renderPhoto(photo);
    }

    #personComparisons() {
        return new Map(
            (this.photoComparison?.persons ?? []).map((comparison) => [
                comparison.label_number,
                comparison,
            ]),
        );
    }

    #setCommentCounts(comments) {
        this.commentCounts.clear();
        for (const comment of comments) {
            if (comment.person_id === null) continue;
            const count = this.commentCounts.get(comment.person_id) ?? 0;
            this.commentCounts.set(comment.person_id, count + 1);
        }
    }

    #replacePerson(updated) {
        this.persons = this.persons.map((person) => person.id === updated.id ? updated : person);
    }

    #selectedPerson() {
        return this.persons.find((person) => person.id === this.selectedPersonId) ?? null;
    }

    #updateActions() {
        const removeButton = document.querySelector("#delete-person-label");
        const commentInput = document.querySelector("#comment-content");
        if (removeButton) {
            removeButton.disabled = !this.canManageLabels
                || this.selectedPersonId === null;
        }
        if (commentInput instanceof HTMLTextAreaElement) {
            commentInput.disabled = !this.canContribute
                || this.selectedPersonId === null;
        }
    }

    async #runAction(message, action) {
        this.#setStatus(message, true);
        try {
            await action();
            this.#setStatus("Opgeslagen", false);
        } catch (error) {
            this.#showError(error.message);
            this.#setStatus("Opslaan mislukt", false);
        }
    }

    #setStatus(message, busy) {
        const status = document.querySelector("#save-status");
        if (!status) return;
        status.textContent = message;
        status.classList.toggle("is-busy", busy);
    }

    #showError(message) {
        const error = document.querySelector("#error-message");
        const text = document.querySelector("#error-message-text");
        if (!error || !text) return;
        text.textContent = message;
        error.hidden = false;
    }

    #hideError() {
        const error = document.querySelector("#error-message");
        if (error) error.hidden = true;
    }

    showInitializationError(message) {
        document.querySelector("#loading-message")?.setAttribute("hidden", "");
        this.#showError(message);
    }

    #showContent() {
        document.querySelector("#loading-message").hidden = true;
        document.querySelector("#photo-content").hidden = false;
    }
}
