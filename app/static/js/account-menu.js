"use strict";

const toggle = document.querySelector("#account-menu-toggle");
const panel = document.querySelector("#account-menu-panel");

if (toggle instanceof HTMLButtonElement && panel instanceof HTMLElement) {
    toggle.addEventListener("click", () => {
        const willOpen = panel.hidden;
        panel.hidden = !willOpen;
        toggle.setAttribute("aria-expanded", String(willOpen));
        if (willOpen) {
            const firstField = panel.querySelector("input:not([type='hidden'])");
            if (firstField instanceof HTMLInputElement) firstField.focus();
        }
    });

    document.addEventListener("click", (event) => {
        if (panel.hidden) return;
        const target = event.target;
        if (!(target instanceof Node)) return;
        if (panel.contains(target) || toggle.contains(target)) return;
        closeMenu();
    });

    window.addEventListener("keydown", (event) => {
        if (event.key !== "Escape" || panel.hidden) return;
        closeMenu();
        toggle.focus();
    });
}

function closeMenu() {
    if (!(toggle instanceof HTMLButtonElement) || !(panel instanceof HTMLElement)) return;
    panel.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
}
