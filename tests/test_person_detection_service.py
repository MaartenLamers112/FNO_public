"""Tests voor automatisch labelen met gezichtsdetectie."""

from __future__ import annotations

import numpy as np

from app.extensions import db
from app.models import Person, Photo
from app.services.person_detection_service import FaceCandidate, PersonDetectionService


class FakeDetector:
    """Eenvoudige OpenVINO-detector voor servicetests."""

    def detect(self, image):
        """Geef twee vaste gezichtsdetecties terug."""

        del image
        return [
            FaceCandidate(100, 100, 200, 120, 0.91),
            FaceCandidate(500, 120, 200, 120, 0.78),
        ]


def test_auto_label_creates_real_labels(app, monkeypatch) -> None:
    """Detectie maakt echte opeenvolgende labels aan."""

    with app.app_context():
        photo = Photo(mm_id="mm-detect", photo_number="D1")
        db.session.add(photo)
        db.session.commit()

        service = PersonDetectionService(detector=FakeDetector())
        monkeypatch.setattr(
            service,
            "_decode_image",
            lambda image_bytes: np.zeros((1000, 1000, 3), dtype=np.uint8),
        )

        result = service.auto_label(photo_id=photo.id, image_bytes=b"image")

        assert result.detected_count == 2
        assert result.created_count == 2
        assert result.skipped_existing_count == 0
        assert [person.label_number for person in result.persons] == [1, 2]
        assert [person.x_position for person in result.persons] == [0.2, 0.6]
        assert db.session.query(Person).count() == 2


def test_auto_label_skips_existing_label(app, monkeypatch) -> None:
    """Een detectie nabij een bestaand label maakt geen duplicaat."""

    with app.app_context():
        photo = Photo(mm_id="mm-existing", photo_number="D2")
        db.session.add(photo)
        db.session.flush()
        db.session.add(
            Person(
                photo_id=photo.id,
                label_number=1,
                x_position=0.2,
                y_position=0.07,
            )
        )
        db.session.commit()

        service = PersonDetectionService(detector=FakeDetector())
        monkeypatch.setattr(
            service,
            "_decode_image",
            lambda image_bytes: np.zeros((1000, 1000, 3), dtype=np.uint8),
        )

        result = service.auto_label(photo_id=photo.id, image_bytes=b"image")

        assert result.detected_count == 2
        assert result.created_count == 1
        assert result.skipped_existing_count == 1
        assert [person.label_number for person in result.persons] == [1, 2]


def test_candidates_are_converted_to_relative_label_positions(app) -> None:
    """Gezichtsboxes worden naar posities midden boven het gezicht vertaald."""

    with app.app_context():
        candidates = [FaceCandidate(20, 40, 40, 20, 0.90)]

        result = PersonDetectionService._candidates_to_positions(
            candidates,
            image_width=200,
            image_height=100,
        )

        assert result == [(0.2, 0.35, 0.90)]
