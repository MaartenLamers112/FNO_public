"""Tests voor DashboardService."""

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.extensions import db
from app.models import Comment, History, Photo
from app.services import DashboardService


def test_dashboard_summary_contains_counts(app) -> None:
    """Het dashboard telt statussen en open opmerkingen."""

    with app.app_context():
        concept = Photo(mm_id="mm-1", photo_number="1")
        published = Photo(
            mm_id="mm-2",
            photo_number="2",
            publication_status=PublicationStatus.PUBLISHED,
        )
        hidden = Photo(
            mm_id="mm-3",
            photo_number="3",
            publication_status=PublicationStatus.HIDDEN,
        )
        db.session.add_all([concept, published, hidden])
        db.session.flush()
        db.session.add(
            Comment(
                photo_id=concept.id,
                author_type="visitor",
                content="Open opmerking",
                status="open",
            )
        )
        db.session.add(
            History(
                photo_id=concept.id,
                event_type=HistoryEventType.METADATA_CHANGED,
                description="Beschrijving gewijzigd",
            )
        )
        db.session.commit()

        summary = DashboardService().get_summary()

        assert summary.concept_photos == 1
        assert summary.published_photos == 1
        assert summary.hidden_photos == 1
        assert summary.open_comments == 1
        assert len(summary.recent_activity) == 1
