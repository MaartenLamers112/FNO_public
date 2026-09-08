"use strict";

function addPasswordVisibilityToggle(input) {
    if (!(input instanceof HTMLInputElement)) return;
    if (input.dataset.passwordVisibilityReady === "true") return;

    input.dataset.passwordVisibilityReady = "true";

    const wrapper = document.createElement("span");
    wrapper.className = "password-input-wrapper";
    input.before(wrapper);
    wrapper.append(input);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "password-visibility-button";
    button.textContent = "ðŸ‘";
    button.title = "Wachtwoord tonen";
    button.setAttribute("aria-label", "Wachtwoord tonen");
    button.setAttribute("aria-pressed", "false");

    button.addEventListener("click", () => {
        const showPassword = input.type === "password";

        input.type = showPassword ? "text" : "password";
        button.textContent = showPassword ? "ðŸ™ˆ" : "ðŸ‘";
        button.title = showPassword
            ? "Wachtwoord verbergen"
            : "Wachtwoord tonen";
        button.setAttribute(
            "aria-label",
            showPassword
                ? "Wachtwoord verbergen"
                : "Wachtwoord tonen",
        );
        button.setAttribute("aria-pressed", String(showPassword));
        input.focus({ preventScroll: true });
    });

    wrapper.append(button);
}

for (const input of document.querySelectorAll('input[type="password"]')) {
    addPasswordVisibilityToggle(input);
}