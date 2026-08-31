"use strict";

function waitForViewer(viewer, timeoutMs = 1200) {
    return new Promise((resolve) => {
        let finished = false;
        const finish = () => {
            if (finished) return;
            finished = true;
            resolve();
        };
        viewer.addOnceHandler("animation-finish", finish);
        viewer.addOnceHandler("tile-drawn", finish);
        window.setTimeout(finish, timeoutMs);
    });
}

function normalizedFilename(value) {
    const safeValue = String(value || "foto")
        .trim()
        .replaceAll(/[^a-zA-Z0-9_-]+/g, "_");
    return safeValue || "foto";
}

function roundedRectangle(context, x, y, width, height, radius) {
    const safeRadius = Math.min(radius, width / 2, height / 2);
    context.beginPath();
    context.roundRect(x, y, width, height, safeRadius);
}

function drawLabel(context, x, y, labelNumber, fontSize) {
    const text = String(labelNumber);
    context.font = `bold ${fontSize}px Arial, sans-serif`;
    const textWidth = context.measureText(text).width;
    const horizontalPadding = Math.max(8, fontSize * 0.55);
    const verticalPadding = Math.max(5, fontSize * 0.35);
    const width = Math.max(
        fontSize + horizontalPadding * 2,
        textWidth + horizontalPadding * 2,
    );
    const height = fontSize + verticalPadding * 2;
    const left = x - width / 2;
    const top = y - height / 2;

    roundedRectangle(
        context,
        left,
        top,
        width,
        height,
        Math.max(4, fontSize * 0.3),
    );
    context.fillStyle = "#15191c";
    context.fill();
    context.lineWidth = Math.max(1.5, fontSize * 0.12);
    context.strokeStyle = "#ffffff";
    context.stroke();

    context.fillStyle = "#ffffff";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(text, x, y + 0.5);
}

function downloadCanvas(canvas, filename) {
    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/jpeg", 0.92);
    link.click();
}

export async function exportPhotoWithLabels({
    viewer,
    persons,
    photoNumber,
    labelFontSize = 14,
    showLabels = true,
}) {
    if (!viewer?.viewport || !viewer?.drawer?.canvas) {
        throw new Error("De fotoviewer is nog niet gereed voor export.");
    }

    const tiledImage = viewer.world?.getItemAt(0);
    if (!tiledImage) {
        throw new Error("De foto is nog niet volledig geladen.");
    }

    const center = viewer.viewport.getCenter();
    const zoom = viewer.viewport.getZoom();
    viewer.viewport.goHome(false);
    await waitForViewer(viewer);

    try {
        const sourceCanvas = viewer.drawer.canvas;
        const output = document.createElement("canvas");
        output.width = sourceCanvas.width;
        output.height = sourceCanvas.height;
        const context = output.getContext("2d");
        if (!context) throw new Error("De foto-export kon niet worden opgebouwd.");

        context.drawImage(sourceCanvas, 0, 0);
        const contentSize = tiledImage.getContentSize();
        const scaleX = output.width / viewer.container.clientWidth;
        const scaleY = output.height / viewer.container.clientHeight;
        const fontSize = Math.max(10, Number(labelFontSize) || 14) * scaleY;

        if (showLabels) for (const person of persons) {
            const imagePoint = new OpenSeadragon.Point(
                person.x_position * contentSize.x,
                person.y_position * contentSize.y,
            );
            const viewportPoint =
                viewer.viewport.imageToViewportCoordinates(imagePoint);
            const pixel = viewer.viewport.pixelFromPoint(viewportPoint, true);
            drawLabel(
                context,
                pixel.x * scaleX,
                pixel.y * scaleY,
                person.label_number,
                fontSize,
            );
        }

        downloadCanvas(
            output,
            `${normalizedFilename(photoNumber)}_met_labels.jpg`,
        );
    } finally {
        viewer.viewport.panTo(center, true);
        viewer.viewport.zoomTo(zoom, null, true);
        viewer.viewport.applyConstraints(true);
    }
}
