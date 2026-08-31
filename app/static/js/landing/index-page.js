"use strict";

import { get, patch } from "../api.js";
import {
    loadState,
    restoreScrollPosition,
    saveScrollPosition,
    saveState,
} from "./state.js";
import { renderLocationOptions, renderPhotos } from "./render.js";
import { preferredPhotoId, storePhotoContext } from "../navigation-context.js";

const SEARCH_DELAY_MS = 300;

class LandingPageController {
    constructor(root) {
        this.root = root;
        this.state = loadState();
        this.#applyUrlState();
        this.searchTimer = null;
        this.canManagePublication = root.dataset.canManagePublication === "true";
        this.canViewComparison = root.dataset.canViewComparison === "true";

        this.elements = {
            search: root.querySelector("#photo-search"),
            status: root.querySelector("#photo-status-filter"),
            location: root.querySelector("#photo-location-filter"),
            sort: root.querySelector("#photo-sort"),
            direction: root.querySelector("#photo-sort-direction"),
            viewButtons: [...root.querySelectorAll("[data-view]")],
            results: root.querySelector("#photo-results"),
            loading: root.querySelector("#landing-loading"),
            error: root.querySelector("#landing-error"),
        };
    }


    #applyUrlState() {
        const query = new URLSearchParams(window.location.search);
        for (const key of ["search", "status", "location", "sort", "direction"]) {
            if (query.has(key)) this.state[key] = query.get(key) ?? "";
        }
        if ([...query.keys()].length > 0) saveState(this.state);
    }

    async initialize() {
        this.#applyStateToControls();
        this.#bindEvents();
        await this.#loadPhotos();
        restoreScrollPosition();
    }

    #applyStateToControls() {
        this.elements.search.value = this.state.search;
        this.elements.status.value = this.state.status;
        this.elements.sort.value = this.state.sort;
        this.elements.direction.value = this.state.direction;
        this.#updateViewButtons();
    }

    #bindEvents() {
        this.elements.search.addEventListener("input", () => {
            clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(() => {
                this.state.search = this.elements.search.value.trim();
                void this.#stateChanged();
            }, SEARCH_DELAY_MS);
        });

        this.elements.status.addEventListener("change", () => {
            this.state.status = this.elements.status.value;
            void this.#stateChanged();
        });

        this.elements.location.addEventListener("change", () => {
            this.state.location = this.elements.location.value;
            void this.#stateChanged();
        });

        this.elements.sort.addEventListener("change", () => {
            this.state.sort = this.elements.sort.value;
            void this.#stateChanged();
        });

        this.elements.direction.addEventListener("change", () => {
            this.state.direction = this.elements.direction.value;
            void this.#stateChanged();
        });

        for (const button of this.elements.viewButtons) {
            button.addEventListener("click", () => {
                this.state.view = button.dataset.view;
                saveState(this.state);
                this.#updateViewButtons();
                void this.#loadPhotos();
            });
        }

        this.elements.results.addEventListener("click", (event) => {
            if (event.target.closest("[data-photo-link]")) {
                saveScrollPosition();
            }
        });

        this.elements.results.addEventListener("change", (event) => {
            const checkbox = event.target.closest("[data-photo-visibility]");
            if (!(checkbox instanceof HTMLInputElement)) return;
            void this.#changeVisibility(checkbox);
        });
    }

    async #stateChanged() {
        saveState(this.state);
        await this.#loadPhotos();
    }

    async #loadPhotos() {
        this.#setLoading(true);
        this.#showError("");

        try {
            const data = await get(`/api/photos?${this.#buildQuery()}`);
            this.#updatePhotoTab(data.items);
            renderLocationOptions(
                this.elements.location,
                data.locations,
                this.state.location,
            );
            this.state.location = this.elements.location.value;
            renderPhotos(
                this.elements.results,
                data.items,
                this.state.view,
                {
                    canManagePublication: this.canManagePublication,
                    canViewComparison: this.canViewComparison,
                },
            );
        } catch (error) {
            this.#showError(error.message);
            this.elements.results.replaceChildren();
        } finally {
            this.#setLoading(false);
        }
    }

    async #changeVisibility(checkbox) {
        checkbox.disabled = true;
        try {
            await patch(`/api/photos/${checkbox.dataset.photoId}/management`, {
                is_visible: checkbox.checked,
                is_complete: checkbox.dataset.isComplete === "true",
            });
        } catch (error) {
            checkbox.checked = !checkbox.checked;
            this.#showError(error.message);
        } finally {
            checkbox.disabled = false;
        }
    }

    #buildQuery() {
        const query = new URLSearchParams();

        for (const key of ["search", "status", "location", "sort", "direction"]) {
            if (this.state[key]) {
                query.set(key, this.state[key]);
            }
        }

        return query.toString();
    }

    #updateViewButtons() {
        for (const button of this.elements.viewButtons) {
            const active = button.dataset.view === this.state.view;
            button.classList.toggle("view-button--active", active);
            button.setAttribute("aria-pressed", String(active));
        }
    }

    #updatePhotoTab(items) {
        const photoTab = document.querySelector("[data-photo-tab]");
        if (!(photoTab instanceof HTMLAnchorElement)) return;

        const ids = storePhotoContext(items);
        const targetPhotoId = preferredPhotoId(ids);
        if (!targetPhotoId) {
            photoTab.classList.add("is-disabled");
            photoTab.setAttribute("aria-disabled", "true");
            photoTab.href = "/";
            return;
        }

        photoTab.classList.remove("is-disabled");
        photoTab.removeAttribute("aria-disabled");
        photoTab.href = `/photos/${targetPhotoId}`;
    }

    #setLoading(loading) {
        this.elements.loading.hidden = !loading;
        this.elements.results.setAttribute("aria-busy", String(loading));
    }

    #showError(message) {
        this.elements.error.hidden = !message;
        this.elements.error.textContent = message;
    }
}

const root = document.querySelector("#landing-page");

if (root) {
    const controller = new LandingPageController(root);
    void controller.initialize();
}
