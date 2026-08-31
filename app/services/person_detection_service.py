"""AI-ondersteunde detectie van gezichten op foto's."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import hypot
from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any, Protocol

from flask import current_app

from app.exceptions import ExternalServiceError, NotFoundError, ValidationError
from app.repositories import PersonRepository, PhotoRepository

_DETECTION_LOCK = Lock()


@dataclass(frozen=True, slots=True)
class FaceCandidate:
    """Eén gedetecteerd gezicht in broncoördinaten."""

    x: float
    y: float
    width: float
    height: float
    confidence: float


class FaceDetector(Protocol):
    """Minimale interface van een lokale gezichtsdetector."""

    def detect(self, image: Any) -> list[FaceCandidate]:
        """Detecteer gezichten in één BGR-afbeelding."""


@dataclass(frozen=True, slots=True)
class AutoLabelResult:
    """Samenvatting van automatisch aangemaakte labels."""

    persons: list[Any]
    detected_count: int
    created_count: int
    skipped_existing_count: int
    model_name: str
    source_width: int
    source_height: int
    analysis_width: int
    analysis_height: int
    detection_passes: int
    image_load_duration_ms: int
    detector_load_duration_ms: int
    inference_duration_ms: int
    duration_ms: int


class OpenVinoFaceDetector:
    """Voer face-detection-retail-0004 lokaal uit via OpenVINO."""

    def __init__(self, model_path: Path, confidence_threshold: float) -> None:
        """Laad en compileer het OpenVINO-model voor de CPU."""

        if not model_path.exists():
            raise ExternalServiceError(
                "Het OpenVINO-gezichtsmodel ontbreekt.",
                code="PERSON_DETECTION_MODEL_MISSING",
                details={"model_path": str(model_path)},
            )

        weights_path = model_path.with_suffix(".bin")
        if not weights_path.exists():
            raise ExternalServiceError(
                "De OpenVINO-modelgewichten ontbreken.",
                code="PERSON_DETECTION_MODEL_MISSING",
                details={"model_path": str(weights_path)},
            )

        try:
            from openvino import Core
        except ImportError as exc:
            raise ExternalServiceError(
                "OpenVINO is niet geïnstalleerd voor gezichtsdetectie.",
                code="PERSON_DETECTION_UNAVAILABLE",
            ) from exc

        try:
            core = Core()
            model = core.read_model(
                model=str(model_path),
                weights=str(weights_path),
            )
            self.compiled_model = core.compile_model(model, "CPU")
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
        except Exception as exc:
            raise ExternalServiceError(
                "Het OpenVINO-gezichtsmodel kon niet worden geladen.",
                code="PERSON_DETECTION_MODEL_FAILED",
            ) from exc

        input_shape = list(self.input_layer.shape)
        self.input_height = int(input_shape[2])
        self.input_width = int(input_shape[3])
        self.confidence_threshold = confidence_threshold

    def detect(self, image: Any) -> list[FaceCandidate]:
        """Detecteer gezichten en reken boxes terug naar de bronafbeelding."""

        try:
            import cv2
        except ImportError as exc:
            raise ExternalServiceError(
                "OpenCV is niet geïnstalleerd voor gezichtsdetectie.",
                code="PERSON_DETECTION_UNAVAILABLE",
            ) from exc

        image_height, image_width = image.shape[:2]
        resized = cv2.resize(
            image,
            (self.input_width, self.input_height),
            interpolation=cv2.INTER_AREA,
        )
        blob = resized.transpose((2, 0, 1))[None, ...]

        with _DETECTION_LOCK:
            raw_output = self.compiled_model([blob])[self.output_layer]

        candidates: list[FaceCandidate] = []
        for item in raw_output.reshape(-1, 7):
            confidence = float(item[2])
            if confidence < self.confidence_threshold:
                continue

            x1 = max(0.0, min(1.0, float(item[3]))) * image_width
            y1 = max(0.0, min(1.0, float(item[4]))) * image_height
            x2 = max(0.0, min(1.0, float(item[5]))) * image_width
            y2 = max(0.0, min(1.0, float(item[6]))) * image_height
            width = max(1.0, x2 - x1)
            height = max(1.0, y2 - y1)

            candidates.append(
                FaceCandidate(
                    x=x1,
                    y=y1,
                    width=width,
                    height=height,
                    confidence=confidence,
                )
            )

        return candidates


class PersonDetectionService:
    """Detecteer gezichten en maak alleen ontbrekende labels aan."""

    def __init__(
        self,
        *,
        photo_repository: PhotoRepository | None = None,
        person_repository: PersonRepository | None = None,
        detector: FaceDetector | None = None,
    ) -> None:
        """Initialiseer de detectieservice."""

        self.photo_repository = photo_repository or PhotoRepository()
        self.person_repository = person_repository or PersonRepository()
        self.detector = detector

    def auto_label(
        self,
        *,
        photo_id: int,
        image_bytes: bytes,
        user_id: int | None = None,
    ) -> AutoLabelResult:
        """Detecteer gezichten en sla ontbrekende labels direct op."""

        from app.services.person_service import PersonService

        started_at = perf_counter()
        if self.photo_repository.get(photo_id) is None:
            raise NotFoundError(
                "De foto bestaat niet.",
                code="PHOTO_NOT_FOUND",
                details={"photo_id": photo_id},
            )

        image_started_at = perf_counter()
        image = self._decode_image(image_bytes)
        image_load_duration_ms = round((perf_counter() - image_started_at) * 1000)
        image_height, image_width = image.shape[:2]

        detector_started_at = perf_counter()
        detector = self.detector or self._load_detector(
            current_app.config["PERSON_DETECTION_MODEL_PATH"],
            current_app.config["PERSON_DETECTION_CONFIDENCE_THRESHOLD"],
        )
        detector_load_duration_ms = round((perf_counter() - detector_started_at) * 1000)

        inference_started_at = perf_counter()
        try:
            candidates = detector.detect(image)
        except ExternalServiceError:
            raise
        except Exception as exc:
            raise ExternalServiceError(
                "De gezichtsdetectie kon niet worden uitgevoerd.",
                code="PERSON_DETECTION_FAILED",
            ) from exc
        inference_duration_ms = round((perf_counter() - inference_started_at) * 1000)

        candidates = sorted(
            candidates,
            key=lambda candidate: candidate.confidence,
            reverse=True,
        )[: current_app.config["PERSON_DETECTION_MAX_RESULTS"]]
        positions = self._candidates_to_positions(candidates, image_width, image_height)
        existing = self.person_repository.get_by_photo(photo_id)
        new_positions, skipped = self._exclude_existing(positions, existing)
        ordered_positions = self._order_positions(new_positions)

        if ordered_positions:
            PersonService().create_labels_from_detections(
                photo_id=photo_id,
                positions=[(item[0], item[1]) for item in ordered_positions],
                user_id=user_id,
            )

        persons = self.person_repository.get_by_photo(photo_id)
        return AutoLabelResult(
            persons=persons,
            detected_count=len(candidates),
            created_count=len(ordered_positions),
            skipped_existing_count=skipped,
            model_name="OpenVINO face-detection-retail-0004",
            source_width=image_width,
            source_height=image_height,
            analysis_width=image_width,
            analysis_height=image_height,
            detection_passes=1,
            image_load_duration_ms=image_load_duration_ms,
            detector_load_duration_ms=detector_load_duration_ms,
            inference_duration_ms=inference_duration_ms,
            duration_ms=round((perf_counter() - started_at) * 1000),
        )

    @staticmethod
    def _decode_image(image_bytes: bytes) -> Any:
        """Decodeer de door de browser aangeleverde JPEG of PNG."""

        if not image_bytes:
            raise ValidationError(
                "De afbeelding voor Auto label ontbreekt.",
                code="PERSON_DETECTION_IMAGE_REQUIRED",
            )
        if len(image_bytes) > 8 * 1024 * 1024:
            raise ValidationError(
                "De afbeelding voor Auto label is te groot.",
                code="PERSON_DETECTION_IMAGE_TOO_LARGE",
            )
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise ExternalServiceError(
                "OpenCV en NumPy zijn niet geïnstalleerd voor gezichtsdetectie.",
                code="PERSON_DETECTION_UNAVAILABLE",
            ) from exc
        encoded = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise ValidationError(
                "De afbeelding voor Auto label kon niet worden gelezen.",
                code="PERSON_DETECTION_IMAGE_INVALID",
            )
        return image

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_detector(
        model_path: str,
        confidence_threshold: float,
    ) -> OpenVinoFaceDetector:
        """Laad het OpenVINO-model één keer per proces."""

        return OpenVinoFaceDetector(Path(model_path), confidence_threshold)

    @staticmethod
    def _candidates_to_positions(
        candidates: list[FaceCandidate],
        image_width: int,
        image_height: int,
    ) -> list[tuple[float, float, float]]:
        """Plaats labels midden boven ieder gevonden gezicht."""

        margin_factor = current_app.config["PERSON_DETECTION_LABEL_MARGIN"]
        positions: list[tuple[float, float, float]] = []
        for candidate in candidates:
            label_margin = max(candidate.height * margin_factor, 2.0)
            x_position = min(
                max((candidate.x + candidate.width / 2) / image_width, 0.0),
                1.0,
            )
            y_position = min(
                max((candidate.y - label_margin) / image_height, 0.0),
                1.0,
            )
            positions.append((x_position, y_position, candidate.confidence))
        return positions

    @staticmethod
    def _exclude_existing(
        positions: list[tuple[float, float, float]],
        existing: list[Any],
    ) -> tuple[list[tuple[float, float, float]], int]:
        """Sla detecties over die al nabij een bestaand label liggen."""

        minimum_distance = current_app.config["PERSON_DETECTION_EXISTING_RADIUS"]
        filtered: list[tuple[float, float, float]] = []
        skipped = 0
        for position in positions:
            nearby = any(
                hypot(
                    position[0] - float(person.x_position),
                    position[1] - float(person.y_position),
                )
                <= minimum_distance
                for person in existing
            )
            if nearby:
                skipped += 1
            else:
                filtered.append(position)
        return filtered, skipped

    @staticmethod
    def _order_positions(
        positions: list[tuple[float, float, float]],
    ) -> list[tuple[float, float, float]]:
        """Sorteer detecties per globale rij en daarna van links naar rechts."""

        return sorted(
            positions,
            key=lambda position: (round(position[1] / 0.08), position[0]),
        )
