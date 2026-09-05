"""Repository voor aanvragen om een hogere gebruikersrol."""

from __future__ import annotations

from sqlalchemy import func, select

from app.extensions import db
from app.models import RoleUpgradeRequest
from app.models.mixins import utc_now
from app.repositories.base_repository import BaseRepository


class RoleUpgradeRequestRepository(BaseRepository[RoleUpgradeRequest]):
    """Databasebewerkingen voor rolverhogingsaanvragen."""

    model = RoleUpgradeRequest

    def create_request(
        self, *, user_id: int, requested_role: str
    ) -> RoleUpgradeRequest:
        """Maak een openstaande rolverhogingsaanvraag."""

        return self.add(
            RoleUpgradeRequest(
                user_id=user_id,
                requested_role=requested_role,
                status="pending",
            )
        )

    def get_pending_for_user(self, user_id: int) -> RoleUpgradeRequest | None:
        """Geef de openstaande aanvraag van een gebruiker terug."""

        statement = (
            select(RoleUpgradeRequest)
            .where(
                RoleUpgradeRequest.user_id == user_id,
                RoleUpgradeRequest.status == "pending",
            )
            .order_by(RoleUpgradeRequest.requested_at.desc())
            .limit(1)
        )
        return db.session.scalar(statement)

    def get_all_recent(self) -> list[RoleUpgradeRequest]:
        """Geef alle aanvragen terug, nieuwste eerst."""

        statement = select(RoleUpgradeRequest).order_by(
            RoleUpgradeRequest.requested_at.desc(),
            RoleUpgradeRequest.id.desc(),
        )
        return list(db.session.scalars(statement))

    def count_pending(self) -> int:
        """Tel openstaande aanvragen."""

        statement = (
            select(func.count())
            .select_from(RoleUpgradeRequest)
            .where(RoleUpgradeRequest.status == "pending")
        )
        return db.session.scalar(statement) or 0

    def review(
        self,
        request_item: RoleUpgradeRequest,
        *,
        status: str,
        reviewed_by_user_id: int,
        rejection_reason: str | None,
    ) -> RoleUpgradeRequest:
        """Registreer de beoordeling van een aanvraag."""

        request_item.status = status
        request_item.reviewed_at = utc_now()
        request_item.reviewed_by_user_id = reviewed_by_user_id
        request_item.rejection_reason = rejection_reason
        return request_item
