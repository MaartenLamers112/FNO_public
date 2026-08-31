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

function canvasToBlob(canvas) {
    return new Promise((resolve, reject) => {
        try {
            canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                    return;
                }
                reject(new Error("De zichtbare foto kon niet worden voorbereid voor Auto label."));
            }, "image/jpeg", 0.9);
        } catch (error) {
            reject(new Error(
                "De zichtbare foto kan door browserbeveiliging niet worden geanalyseerd.",
                { cause: error },
            ));
        }
    });
}

export async function captureViewerImage(viewer) {
    if (!viewer?.viewport || !viewer?.drawer?.canvas) {
        throw new Error("De fotoviewer is nog niet gereed voor Auto label.");
    }

    const center = viewer.viewport.getCenter();
    const zoom = viewer.viewport.getZoom();

    viewer.viewport.goHome(false);
    await waitForViewer(viewer);

    try {
        return await canvasToBlob(viewer.drawer.canvas);
    } finally {
        viewer.viewport.panTo(center, true);
        viewer.viewport.zoomTo(zoom, null, true);
        viewer.viewport.applyConstraints(true);
    }
}
