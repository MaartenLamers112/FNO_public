"use strict";

import { PhotoPageController } from "./photo-page-controller.js";

document.addEventListener(
    "DOMContentLoaded",
    initializePhotoPage,
);

async function initializePhotoPage() {
    const page = document.querySelector("#photo-page");

    if (!page) return;

    const controller = new PhotoPageController(page);
    try {
        await controller.initialize();
    } catch (error) {
        controller.showInitializationError(
            error instanceof Error ? error.message : "De fotopagina kon niet worden geladen.",
        );
    }
}
