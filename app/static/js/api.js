"use strict";

/**
 * Voer een GET-request uit en geef de JSON terug.
 */
export async function get(url) {
    return requestJson(url, {
        method: "GET",
    });
}

/**
 * Voer een POST-request uit en geef de JSON terug.
 */
export async function post(url, body) {
    return requestJson(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(body),
    });
}


/**
 * Voer een multipart POST-request uit en geef de JSON terug.
 */
export async function postForm(url, formData) {
    return requestJson(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: formData,
    });
}

/**
 * Voer een PATCH-request uit en geef de JSON terug.
 */
export async function patch(url, body) {
    return requestJson(url, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(body),
    });
}


/**
 * Voer een DELETE-request uit.
 */
export async function remove(url) {
    return requestJson(url, {
        method: "DELETE",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
    });
}

async function requestJson(url, options) {
    const response = await fetch(url, {
        ...options,
        headers: {
            Accept: "application/json",
            ...options.headers,
        },
    });

    const data = await parseResponse(response);

    if (!response.ok) {
        throw new Error(
            data?.message
            ?? `De aanvraag is mislukt (${response.status}).`,
        );
    }

    return data;
}

async function parseResponse(response) {
    const contentType =
        response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
        return response.json();
    }

    const text = await response.text();

    if (!text) {
        return null;
    }

    throw new Error(
        `De server gaf geen JSON terug (${response.status}).`,
    );
}

function getCsrfToken() {
    const tokenElement = document.querySelector(
        'meta[name="csrf-token"]',
    );

    const token = tokenElement?.content;

    if (!token) {
        throw new Error(
            "Het CSRF-token ontbreekt.",
        );
    }

    return token;
}