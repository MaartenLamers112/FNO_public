"use strict";

const CONTEXT_KEY = "fno.navigation.photoIds";
const LAST_PHOTO_KEY = "fno.navigation.lastPhotoId";
const FIRST_PHOTO_KEY = "fno.navigation.firstPhotoId";

export function storePhotoContext(items) {
    const ids = items
        .map((item) => String(item.id))
        .filter((id) => /^\d+$/.test(id));
    sessionStorage.setItem(CONTEXT_KEY, JSON.stringify(ids));

    if (ids.length > 0) sessionStorage.setItem(FIRST_PHOTO_KEY, ids[0]);
    else sessionStorage.removeItem(FIRST_PHOTO_KEY);

    return ids;
}

export function getPhotoContextIds() {
    try {
        const value = JSON.parse(sessionStorage.getItem(CONTEXT_KEY) ?? "[]");
        if (!Array.isArray(value)) return [];
        return value.map(String).filter((id) => /^\d+$/.test(id));
    } catch {
        return [];
    }
}

export function rememberPhoto(photoId) {
    const normalized = String(photoId);
    if (!/^\d+$/.test(normalized)) return;
    sessionStorage.setItem(LAST_PHOTO_KEY, normalized);
    localStorage.setItem(LAST_PHOTO_KEY, normalized);
}

export function preferredPhotoId(ids = getPhotoContextIds()) {
    if (ids.length === 0) return null;
    const last = sessionStorage.getItem(LAST_PHOTO_KEY)
        ?? localStorage.getItem(LAST_PHOTO_KEY);
    return last && ids.includes(last) ? last : ids[0];
}

export function contextNeighbours(photoId) {
    const ids = getPhotoContextIds();
    const current = String(photoId);
    const index = ids.indexOf(current);
    if (index < 0) return null;

    return {
        previousPhotoId: index > 0 ? ids[index - 1] : null,
        nextPhotoId: index < ids.length - 1 ? ids[index + 1] : null,
    };
}
