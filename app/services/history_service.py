"""Bedrijfslogica voor historie."""

from __future__ import annotations

from datetime import datetime

from app.enums.history_event_type import HistoryEventType
from app.models import History
from app.repositories import HistoryRepository
from app.services.base_service import BaseService


class HistoryService(BaseService[HistoryRepository]):
    """Service voor het registreren van historie."""

    def __init__(
        self,
        repository: HistoryRepository | None = None,
    ) -> None:
        """Initialiseer de historieservice."""

        super().__init__(repository or HistoryRepository())

    def record(
        self,
        *,
        photo_id: int,
        event_type: HistoryEventType,
        description: str,
        person_id: int | None = None,
        user_id: int | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> None:
        """Registreer een historie-item."""

        self.repository.create(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            event_type=event_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
        )

    def search(
        self,
        *,
        photo_number: str = "",
        event_type: str = "",
        username: str = "",
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> list[History]:
        """Zoek historie voor beheer en export."""

        return self.repository.search(
            photo_number=photo_number,
            event_type=event_type,
            username=username,
            started_at=started_at,
            ended_at=ended_at,
        )
