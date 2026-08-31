"use strict";

export class OverlayManager {
    constructor(viewer) {
        if (!viewer) {
            throw new Error(
                "Een OpenSeadragon-viewer is verplicht.",
            );
        }

        this.viewer = viewer;

        /**
         * Map<
         *   overlayId,
         *   {
         *     element,
         *     metadata,
         *   }
         * >
         */
        this.overlays = new Map();
    }

    add({
        id,
        element,
        location,
        placement,
        metadata = {},
    }) {
        this.#validateId(id);
        this.#validateElement(element);
        this.#validateLocation(location);

        if (this.overlays.has(id)) {
            throw new Error(
                `Overlay '${id}' bestaat al.`,
            );
        }

        element.dataset.overlayId = id;

        this.viewer.addOverlay({
            element,
            location,
            placement,
        });

        this.overlays.set(id, {
            element,
            metadata,
        });

        return element;
    }

    update({
        id,
        location,
        placement,
    }) {
        this.#validateId(id);
        this.#validateLocation(location);

        const overlay =
            this.overlays.get(id);

        if (!overlay) {
            throw new Error(
                `Overlay '${id}' bestaat niet.`,
            );
        }

        this.viewer.updateOverlay(
            overlay.element,
            location,
            placement,
        );
    }

    get(id) {
        this.#validateId(id);

        return (
            this.overlays.get(id) ?? null
        );
    }

    getElement(id) {
        const overlay =
            this.get(id);

        return overlay
            ? overlay.element
            : null;
    }

    getMetadata(id) {
        const overlay =
            this.get(id);

        return overlay
            ? overlay.metadata
            : null;
    }

    has(id) {
        this.#validateId(id);

        return this.overlays.has(id);
    }

    remove(id) {
        this.#validateId(id);

        const overlay =
            this.overlays.get(id);

        if (!overlay) {
            return false;
        }

        this.viewer.removeOverlay(
            overlay.element,
        );

        this.overlays.delete(id);

        return true;
    }

    clear() {
        for (
            const overlay
            of this.overlays.values()
        ) {
            this.viewer.removeOverlay(
                overlay.element,
            );
        }

        this.overlays.clear();
    }

    destroy() {
        this.clear();
        this.viewer = null;
    }

    #validateId(id) {
        if (
            typeof id !== "string"
            || id.trim() === ""
        ) {
            throw new Error(
                "Een overlay-ID is verplicht.",
            );
        }
    }

    #validateElement(element) {
        if (
            !(element instanceof HTMLElement)
        ) {
            throw new Error(
                "Een geldig overlay-element is verplicht.",
            );
        }
    }

    #validateLocation(location) {
        if (!location) {
            throw new Error(
                "Een overlaylocatie is verplicht.",
            );
        }
    }
}