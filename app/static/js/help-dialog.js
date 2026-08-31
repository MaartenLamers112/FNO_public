"use strict";

document.addEventListener("DOMContentLoaded", initializeHelpDialog);

function initializeHelpDialog() {
    const openButton = document.querySelector("#open-help-dialog");
    const dialog = document.querySelector("#help-dialog");
    if (!(openButton instanceof HTMLButtonElement) || !(dialog instanceof HTMLDialogElement)) {
        return;
    }

    openButton.addEventListener("click", () => showHelpDialog(dialog));
    dialog.addEventListener("click", (event) => closeOnBackdrop(event, dialog));
}

function showHelpDialog(dialog) {
    if (!dialog.open) dialog.showModal();
}

function closeOnBackdrop(event, dialog) {
    if (event.target === dialog) dialog.close();
}

