"use strict";

const DRAG_THRESHOLD_PIXELS = 4;
const DRAGGING_CLASS = "person-label-dragging";

export class DragManager {
    constructor(
        viewer,
        overlayManager,
    ) {
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

        this.viewer = viewer;
        this.overlayManager = overlayManager;

        this.activeDrag = null;

        this.handlePointerMove =
            this.#handlePointerMove.bind(this);

        this.handlePointerUp =
            this.#handlePointerUp.bind(this);

        window.addEventListener(
            "pointermove",
            this.handlePointerMove,
            true,
        );

        window.addEventListener(
            "pointerup",
            this.handlePointerUp,
            true,
        );

        window.addEventListener(
            "pointercancel",
            this.handlePointerUp,
            true,
        );
    }

    register({
        overlayId,
        element,
        onDragStart = null,
        onDragEnd = null,
    }) {
        if (
            typeof overlayId !== "string"
            || overlayId.trim() === ""
        ) {
            throw new Error(
                "Een overlay-ID is verplicht.",
            );
        }

        if (!(element instanceof HTMLElement)) {
            throw new Error(
                "Een geldig overlay-element is verplicht.",
            );
        }

        this.#validateCallback(
            onDragStart,
            "De drag-startcallback",
        );

        this.#validateCallback(
            onDragEnd,
            "De drag-eindcallback",
        );

        element.addEventListener(
            "pointerdown",
            (event) => {
                this.#startDrag({
                    event,
                    overlayId,
                    element,
                    onDragStart,
                    onDragEnd,
                });
            },
        );
    }

    destroy() {
        this.#finishActiveDrag();

        window.removeEventListener(
            "pointermove",
            this.handlePointerMove,
            true,
        );

        window.removeEventListener(
            "pointerup",
            this.handlePointerUp,
            true,
        );

        window.removeEventListener(
            "pointercancel",
            this.handlePointerUp,
            true,
        );

        this.viewer = null;
        this.overlayManager = null;
    }

    #startDrag({
        event,
        overlayId,
        element,
        onDragStart,
        onDragEnd,
    }) {
        if (
            event.pointerType === "mouse"
            && event.button !== 0
        ) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        this.#finishActiveDrag();

        this.activeDrag = {
            overlayId,
            element,
            pointerId: event.pointerId,
            startClientX: event.clientX,
            startClientY: event.clientY,
            moved: false,
            lastViewportPoint: null,
            onDragEnd,
        };

        element.setPointerCapture?.(
            event.pointerId,
        );

        element.classList.add(
            DRAGGING_CLASS,
        );

        this.viewer.setMouseNavEnabled(false);

        onDragStart?.(overlayId);
    }

    #handlePointerMove(event) {
        const drag = this.activeDrag;

        if (
            !drag
            || drag.pointerId !== event.pointerId
        ) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        if (!drag.moved) {
            drag.moved =
                this.#hasPassedDragThreshold(
                    event,
                    drag,
                );
        }

        if (!drag.moved) {
            return;
        }

        const viewportPoint =
            this.#getViewportPoint(event);

        this.overlayManager.update({
            id: drag.overlayId,
            location: viewportPoint,
            placement:
                window.OpenSeadragon
                    .Placement.CENTER,
        });

        drag.lastViewportPoint =
            viewportPoint;
    }

    #handlePointerUp(event) {
        const drag = this.activeDrag;

        if (
            !drag
            || drag.pointerId !== event.pointerId
        ) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        const result = {
            overlayId: drag.overlayId,
            moved: drag.moved,
            viewportPoint:
                drag.lastViewportPoint,
        };

        const onDragEnd =
            drag.onDragEnd;

        this.#finishActiveDrag();

        onDragEnd?.(result);
    }

    #finishActiveDrag() {
        if (!this.activeDrag) {
            return;
        }

        const {
            element,
            pointerId,
        } = this.activeDrag;

        element.classList.remove(
            DRAGGING_CLASS,
        );

        if (
            element.hasPointerCapture?.(
                pointerId,
            )
        ) {
            element.releasePointerCapture(
                pointerId,
            );
        }

        this.viewer?.setMouseNavEnabled(true);

        this.activeDrag = null;
    }

    #getViewportPoint(event) {
        const viewerElement =
            this.viewer.container;

        const rect =
            viewerElement.getBoundingClientRect();

        const pixelPoint =
            new window.OpenSeadragon.Point(
                event.clientX - rect.left,
                event.clientY - rect.top,
            );

        return this.viewer.viewport.pointFromPixel(
            pixelPoint,
            true,
        );
    }

    #hasPassedDragThreshold(
        event,
        drag,
    ) {
        const deltaX =
            event.clientX - drag.startClientX;

        const deltaY =
            event.clientY - drag.startClientY;

        return Math.hypot(
            deltaX,
            deltaY,
        ) >= DRAG_THRESHOLD_PIXELS;
    }

    #validateCallback(
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
}