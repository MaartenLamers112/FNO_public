"use strict";

import { OverlayManager } from "./overlay-manager.js";
import {
    destroyViewer,
    getOverlayManager,
    getViewer,
    setOverlayManager,
    setViewer,
} from "./state.js";

export function initializeViewer({
    elementId,
    imageSource,
    prefixUrl,
}) {
    if (!window.OpenSeadragon) {
        throw new Error("OpenSeadragon is niet geladen.");
    }

    if (!document.getElementById(elementId)) {
        throw new Error(`Viewer-element '${elementId}' bestaat niet.`);
    }

    if (!imageSource) {
        throw new Error("De afbeeldingsbron ontbreekt.");
    }

    destroyViewer();

    const viewer = window.OpenSeadragon({
        id: elementId,
        prefixUrl,
        tileSources: imageSource,
        crossOriginPolicy: "Anonymous",
        showNavigator: false,
        visibilityRatio: 1,
        constrainDuringPan: true,
        maxZoomPixelRatio: 8,
    });

    const overlayManager = new OverlayManager(viewer);

    setViewer(viewer);
    setOverlayManager(overlayManager);

    return {
        viewer,
        overlayManager,
    };
}

export function fitViewerToImage() {
    const viewer = getViewer();

    if (!viewer?.viewport) {
        return;
    }

    viewer.viewport.goHome(true);
}

export {
    destroyViewer,
    getOverlayManager,
    getViewer,
};