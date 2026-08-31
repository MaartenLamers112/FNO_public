"use strict";

export function getNormalizedImagePosition({
    tiledImage,
    viewportPoint,
}) {
    const imagePoint =
        tiledImage.viewportToImageCoordinates(
            viewportPoint,
        );

    const imageSize =
        tiledImage.getContentSize();

    return {
        xPosition: clamp(
            imagePoint.x / imageSize.x,
            0,
            1,
        ),
        yPosition: clamp(
            imagePoint.y / imageSize.y,
            0,
            1,
        ),
    };
}

function clamp(value, minimum, maximum) {
    return Math.min(
        maximum,
        Math.max(minimum, value),
    );
}
