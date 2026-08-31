"use strict";

let viewer = null;
let overlayManager = null;

export function getViewer() {
    return viewer;
}

export function setViewer(value) {
    viewer = value;
}

export function getOverlayManager() {
    return overlayManager;
}

export function setOverlayManager(value) {
    overlayManager = value;
}

export function destroyViewer() {
    if (overlayManager) {
        overlayManager.destroy();
        overlayManager = null;
    }

    if (!viewer) {
        return;
    }

    viewer.destroy();
    viewer = null;
}