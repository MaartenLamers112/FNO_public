"use strict";

export function renderComments(
    comments,
    { onEdit = null, onDelete = null } = {},
) {
    const list = document.querySelector("#comments-list");
    const empty = document.querySelector("#comments-empty");
    const details = document.querySelector("#existing-comments");
    const summary = document.querySelector("#existing-comments-summary");
    if (!list || !empty || !details || !summary) {
        throw new Error("Het opmerkingenpaneel ontbreekt.");
    }

    list.replaceChildren();
    empty.hidden = comments.length !== 0;
    details.hidden = comments.length === 0;
    summary.textContent = `Bestaande opmerkingen (${comments.length})`;

    for (const comment of comments) {
        const card = document.createElement("article");
        card.className = "comment-card";

        const content = document.createElement("p");
        content.textContent = comment.content;

        const actions = document.createElement("div");
        actions.className = "comment-actions";

        const edit = document.createElement("button");
        edit.type = "button";
        edit.className = "text-button";
        edit.textContent = "Bewerken";
        edit.addEventListener("click", () => onEdit?.(comment));

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "text-button text-button-danger";
        remove.textContent = "Verwijderen";
        remove.addEventListener("click", () => onDelete?.(comment));

        actions.append(edit, remove);
        card.append(content, actions);
        list.append(card);
    }
}
