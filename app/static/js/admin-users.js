const searchInput = document.querySelector("#user-search");
const table = document.querySelector("#user-table");
const count = document.querySelector("#user-count");
const sortButtons = document.querySelectorAll(".user-sort-button");

function rows() {
    return [...table.querySelectorAll("[data-user-row]")];
}

function updateCount() {
    const visible = rows().filter((row) => !row.hidden).length;
    count.textContent = `${visible} gebruiker${visible === 1 ? "" : "s"}`;
}

function filterRows() {
    const query = searchInput.value.trim().toLocaleLowerCase("nl");

    for (const row of rows()) {
        const haystack = `${row.dataset.username} ${row.dataset.email}`;
        row.hidden = query !== "" && !haystack.includes(query);
    }

    updateCount();
}

function sortRows(key, direction) {
    const multiplier = direction === "asc" ? 1 : -1;
    const body = table.tBodies[0];

    rows()
        .sort((left, right) => {
            const a = left.dataset[key] ?? "";
            const b = right.dataset[key] ?? "";
            return a.localeCompare(b, "nl", {
                numeric: true,
                sensitivity: "base",
            }) * multiplier;
        })
        .forEach((row) => body.append(row));
}

searchInput.addEventListener("input", filterRows);

for (const button of sortButtons) {
    button.addEventListener("click", () => {
        const direction = button.dataset.direction === "asc" ? "desc" : "asc";

        for (const otherButton of sortButtons) {
            delete otherButton.dataset.direction;
        }

        button.dataset.direction = direction;
        sortRows(button.dataset.sort, direction);
    });
}

updateCount();
