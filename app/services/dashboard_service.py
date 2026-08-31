"""Bedrijfslogica voor het beheerdashboard."""

from __future__ import annotations

from dataclasses import dataclass

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.models import History
from app.repositories import CommentRepository, HistoryRepository, PhotoRepository


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    """Samenvatting voor het beheerdashboard."""

    concept_photos: int
    published_photos: int
    hidden_photos: int
    open_comments: int
    recent_activity: list[History]


class DashboardService:
    """Service voor dashboardgegevens."""

    def __init__(
        self,
        photo_repository: PhotoRepository | None = None,
        comment_repository: CommentRepository | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        """Initialiseer de dashboardservice."""

        self.photo_repository = photo_repository or PhotoRepository()
        self.comment_repository = comment_repository or CommentRepository()
        self.history_repository = history_repository or HistoryRepository()

    def get_summary(self, *, activity_limit: int = 10) -> DashboardSummary:
        """Geef de actuele beheersamenvatting terug."""

        important_types = {
            HistoryEventType.METADATA_CHANGED,
            HistoryEventType.PHOTO_IMPORTED,
            HistoryEventType.PHOTO_PUBLISHED,
            HistoryEventType.PHOTO_HIDDEN,
            HistoryEventType.PHOTO_CONCEPT,
            HistoryEventType.PHOTO_VISIBILITY_CHANGED,
            HistoryEventType.PHOTO_COMPLETION_CHANGED,
            HistoryEventType.SYNCHRONIZATION_COMPLETED,
            HistoryEventType.SYNCHRONIZATION_FAILED,
        }
        recent_activity = [
            item
            for item in self.history_repository.get_recent(limit=100)
            if item.event_type in important_types
        ][:activity_limit]

        return DashboardSummary(
            concept_photos=self.photo_repository.count_by_status(
                PublicationStatus.CONCEPT
            ),
            published_photos=self.photo_repository.count_by_status(
                PublicationStatus.PUBLISHED
            ),
            hidden_photos=self.photo_repository.count_by_status(
                PublicationStatus.HIDDEN
            ),
            open_comments=self.comment_repository.count_open(),
            recent_activity=recent_activity,
        )
