"use strict";

import { get } from "./api.js";
import {
    getPhotoContextIds,
    preferredPhotoId,
    rememberPhoto,
    storePhotoContext,
} from "./navigation-context.js";

const photoTab = document.querySelector("[data-photo-tab]");

if (photoTab instanceof HTMLAnchorElement) {
    photoTab.addEventListener("click", (event) => {
        if (photoTab.getAttribute("aria-disabled") === "true") event.preventDefault();
    });
    void initializePhotoTab(photoTab);
}

async function initializePhotoTab(tab) {
    const page = document.querySelector("#photo-page");
    if (page instanceof HTMLElement && page.dataset.photoId) {
        rememberPhoto(page.dataset.photoId);
        enablePhotoTab(tab, page.dataset.photoId);
        return;
    }

    if (document.querySelector("#landing-page")) {
        disablePhotoTab(tab);
        return;
    }

    let ids = getPhotoContextIds();
    try {
        const data = await get("/api/photos?sort=photo_number&direction=asc");
        ids = storePhotoContext(data.items ?? []);
    } catch {
        if (ids.length === 0) {
            disablePhotoTab(tab);
            return;
        }
    }

    const targetPhotoId = preferredPhotoId(ids);
    if (targetPhotoId) enablePhotoTab(tab, targetPhotoId);
    else disablePhotoTab(tab);
}

function enablePhotoTab(tab, photoId) {
    tab.href = `/photos/${photoId}`;
    tab.classList.remove("is-disabled");
    tab.removeAttribute("aria-disabled");
}

function disablePhotoTab(tab) {
    tab.href = "/";
    tab.classList.add("is-disabled");
    tab.setAttribute("aria-disabled", "true");
}
