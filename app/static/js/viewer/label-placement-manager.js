"use strict";

import { getNormalizedImagePosition } from "./coordinates.js";

export class LabelPlacementManager {
    constructor(viewer, onPlace) {
        if (!viewer) {
            throw new Error(
                "Een OpenSeadragon-viewer is verplicht.",
            );
        }

        if (typeof onPlace !== "function") {
            throw new Error(
                "Een plaatsingscallback is verplicht.",
            );
        }

        this.viewer = viewer;
        this.onPlace = onPlace;
        this.enabled = false;

        this.viewer.addHandler(
            "canvas-click",
            (event) => {
                this.#handleCanvasClick(event);
            },
        );
    }

    setEnabled(enabled) {
        this.enabled = Boolean(enabled);

        const canvas = this.viewer.canvas;

        if (canvas) {
            canvas.classList.toggle(
                "photo-viewer--placing-label",
                this.enabled,
            );
        }
    }

    #handleCanvasClick(event) {
        if (!this.enabled || !event.quick) {
            return;
        }

        event.preventDefaultAction = true;

        const tiledImage =
            this.viewer.world.getItemAt(0);

        if (!tiledImage) {
            return;
        }

        const viewportPoint =
            this.viewer.viewport.pointFromPixel(
                event.position,
                true,
            );

        const position =
            getNormalizedImagePosition({
                tiledImage,
                viewportPoint,
            });

        this.onPlace(position);
    }
}
