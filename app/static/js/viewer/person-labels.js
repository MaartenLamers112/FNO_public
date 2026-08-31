"use strict";

import { hasPersonName } from "../person-utils.js";
import { getNormalizedImagePosition } from "./coordinates.js";

const PERSON_OVERLAY_PREFIX = "person-";

const NAMED_CLASS = "person-label--named";
const UNNAMED_CLASS = "person-label--unnamed";
const SELECTED_CLASS = "person-label--selected";

export function renderPersonLabels({
    persons,
    viewer,
    overlayManager,
    dragManager,
    onPersonSelect = null,
    onPersonMove = null,
    displayMode = "numbered",
    showInternalNumbers = false,
}) {
    if (!viewer) {
        throw new Error(
            "Een OpenSeadragon-viewer is verplicht.",
        );
    }

    if (!overlayManager) {
        throw new Error(
            "Een OverlayManager is verplicht.",
        );
    }

    validateCallback(
        onPersonSelect,
        "De selectiecallback",
    );

    validateCallback(
        onPersonMove,
        "De verplaatscallback",
    );

    overlayManager.clear();

    const render = () => {
        const tiledImage =
            viewer.world.getItemAt(0);

        if (!tiledImage) {
            return;
        }

        if (displayMode !== "numbered" && !showInternalNumbers) return;

        for (const person of persons) {
            addPersonLabel({
                person,
                tiledImage,
                overlayManager,
                dragManager,
                onPersonSelect,
                onPersonMove,
            });
        }
    };

    if (viewer.world.getItemCount() > 0) {
        render();
        return;
    }

    viewer.addOnceHandler(
        "open",
        render,
    );
}

export function selectPersonLabel({
    personId,
    overlayManager,
}) {
    if (!overlayManager) {
        throw new Error(
            "Een OverlayManager is verplicht.",
        );
    }

    clearPersonLabelSelection(
        overlayManager,
    );

    const label =
        overlayManager.getElement(
            getPersonOverlayId(personId),
        );

    if (!label) {
        return false;
    }

    label.classList.remove(
        NAMED_CLASS,
        UNNAMED_CLASS,
    );

    label.classList.add(
        SELECTED_CLASS,
    );

    label.setAttribute(
        "aria-pressed",
        "true",
    );

    return true;
}

function addPersonLabel({
    person,
    tiledImage,
    overlayManager,
    dragManager,
    onPersonSelect,
    onPersonMove,
}) {
    const overlayId =
        getPersonOverlayId(person.id);

    const imageSize =
        tiledImage.getContentSize();

    const imagePoint =
        new window.OpenSeadragon.Point(
            person.x_position * imageSize.x,
            person.y_position * imageSize.y,
        );

    const viewportPoint =
        tiledImage.imageToViewportCoordinates(
            imagePoint,
        );

    const element =
        createPersonLabelElement(
            person,
            onPersonSelect,
            Boolean(dragManager),
        );

    overlayManager.add({
        id: overlayId,
        element,
        location: viewportPoint,
        placement:
            window.OpenSeadragon
                .Placement.CENTER,
        metadata: {
            person,
        },
    });

    if (!dragManager) {
        return;
    }

    dragManager.register({
        overlayId,
        element,
        onDragStart: () => {
            onPersonSelect?.(person.id);
        },
        onDragEnd: ({
            moved,
            viewportPoint:
                newViewportPoint,
        }) => {
            if (
                !moved
                || !newViewportPoint
            ) {
                return;
            }

            const newPosition =
                getNormalizedImagePosition({
                    tiledImage,
                    viewportPoint:
                        newViewportPoint,
                });

            onPersonMove?.({
                personId: person.id,
                xPosition:
                    newPosition.xPosition,
                yPosition:
                    newPosition.yPosition,
            });
        },
    });
}

function createPersonLabelElement(
    person,
    onPersonSelect,
    isDraggable,
) {
    const element =
        document.createElement("button");

    element.type = "button";
    element.className = "person-label";
    element.textContent =
        String(person.label_number);

    element.dataset.personId =
        String(person.id);

    element.dataset.labelNumber =
        String(person.label_number);

    element.dataset.personHasName =
        String(hasPersonName(person));

    element.setAttribute(
        "aria-pressed",
        "false",
    );

    element.setAttribute(
        "aria-label",
        getPersonLabelDescription(person),
    );

    applyDefaultLabelState(element);

    if (!isDraggable) {
        element.addEventListener(
            "pointerdown",
            (event) => {
                if (!event.isPrimary) {
                    return;
                }
                stopViewerInteraction(event);
                onPersonSelect?.(person.id);
            },
        );
    }

    element.addEventListener(
        "click",
        (event) => {
            stopViewerInteraction(event);
            if (event.detail === 0) {
                onPersonSelect?.(person.id);
            }
        },
    );

    return element;
}

function clearPersonLabelSelection(
    overlayManager,
) {
    for (
        const overlay
        of overlayManager.overlays.values()
    ) {
        const element =
            overlay.element;

        element.classList.remove(
            SELECTED_CLASS,
        );

        element.setAttribute(
            "aria-pressed",
            "false",
        );

        applyDefaultLabelState(element);
    }
}

function applyDefaultLabelState(element) {
    element.classList.remove(
        NAMED_CLASS,
        UNNAMED_CLASS,
    );

    const hasName =
        element.dataset.personHasName
        === "true";

    element.classList.add(
        hasName
            ? NAMED_CLASS
            : UNNAMED_CLASS,
    );
}

function stopViewerInteraction(event) {
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
}

function validateCallback(
    callback,
    description,
) {
    if (
        callback !== null
        && typeof callback !== "function"
    ) {
        throw new Error(
            `${description} moet een functie zijn.`,
        );
    }
}

function getPersonOverlayId(personId) {
    return `${PERSON_OVERLAY_PREFIX}${personId}`;
}

function getPersonLabelDescription(person) {
    const name =
        person.current_name
        ?? "naam onbekend";

    return (
        `Persoon ${person.label_number}: ${name}`
    );
}