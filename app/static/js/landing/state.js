"use strict";

const STORAGE_KEY = "fno.landing.state";
const SCROLL_KEY = "fno.landing.scrollY";

const DEFAULT_STATE = Object.freeze({
    search: "",
    status: "",
    location: "",
    sort: "photo_number",
    direction: "asc",
    view: "medium",
});

export function loadState() {
    try {
        const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));

        return {
            ...DEFAULT_STATE,
            ...stored,
        };
    } catch {
        return { ...DEFAULT_STATE };
    }
}

export function saveState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export function saveScrollPosition() {
    sessionStorage.setItem(SCROLL_KEY, String(window.scrollY));
}

export function restoreScrollPosition() {
    const scrollY = Number(sessionStorage.getItem(SCROLL_KEY) ?? 0);

    if (Number.isFinite(scrollY) && scrollY > 0) {
        requestAnimationFrame(() => window.scrollTo({ top: scrollY }));
    }
}
