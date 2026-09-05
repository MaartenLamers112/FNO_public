"""Bedrijfslogica voor aanvragen om een hogere gebruikersrol."""

from __future__ import annotations

from flask import current_app

from app.exceptions import AuthorizationError, ValidationError
from app.models import RoleUpgradeRequest, User
from app.repositories import RoleUpgradeRequestRepository, UserRepository
from app.services.mail_service import MailService
from app.services.user_service import UserService


class RoleUpgradeRequestService:
    """Beheer aanvragen en beoordelingen van rolverhogingen."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    ROLE_SEQUENCE = {
        UserService.USER_ROLE_NAME: UserService.EMPLOYEE_ROLE_NAME,
        UserService.EMPLOYEE_ROLE_NAME: UserService.ADMINISTRATOR_ROLE_NAME,
    }
    ROLE_LABELS = {
        UserService.USER_ROLE_NAME: "Gebruiker",
        UserService.EMPLOYEE_ROLE_NAME: "Medewerker",
        UserService.ADMINISTRATOR_ROLE_NAME: "Beheerder",
    }

    def __init__(
        self,
        repository: RoleUpgradeRequestRepository | None = None,
        user_repository: UserRepository | None = None,
        mail_service: MailService | None = None,
    ) -> None:
        """Initialiseer de service."""

        self.repository = repository or RoleUpgradeRequestRepository()
        self.user_repository = user_repository or UserRepository()
        self.mail_service = mail_service or MailService()

    def get_pending_for_user(self, user_id: int) -> RoleUpgradeRequest | None:
        """Geef de openstaande aanvraag van een gebruiker terug."""

        return self.repository.get_pending_for_user(user_id)

    def get_available_upgrade(self, user_id: int) -> str | None:
        """Geef de eerstvolgende rol die kan worden aangevraagd."""

        user = self._get_active_user(user_id)
        return self.ROLE_SEQUENCE.get(user.role.name)

    def request_upgrade(self, user_id: int) -> RoleUpgradeRequest:
        """Maak een aanvraag voor precies één hogere rol."""

        user = self._get_active_user(user_id)
        if user.email is None or not user.email_verified:
            raise ValidationError(
                "Bevestig eerst je e-mailadres voordat je een hogere rol aanvraagt.",
                code="EMAIL_VERIFICATION_REQUIRED",
            )

        requested_role = self.ROLE_SEQUENCE.get(user.role.name)
        if requested_role is None:
            raise ValidationError(
                "Voor je huidige rol kan geen hogere rol worden aangevraagd.",
                code="ROLE_UPGRADE_NOT_AVAILABLE",
            )
        if self.repository.get_pending_for_user(user.id) is not None:
            raise ValidationError(
                "Er staat al een rolverhogingsaanvraag open.",
                code="ROLE_UPGRADE_ALREADY_PENDING",
            )

        request_item = self.repository.create_request(
            user_id=user.id,
            requested_role=requested_role,
        )
        self.repository.save()
        self._notify_administrators(user, request_item)
        return request_item

    def list_requests(self) -> list[RoleUpgradeRequest]:
        """Geef alle aanvragen terug."""

        return self.repository.get_all_recent()

    def count_pending(self) -> int:
        """Tel openstaande aanvragen."""

        return self.repository.count_pending()

    def review_request(
        self,
        request_id: int,
        *,
        reviewer_id: int,
        approve: bool,
        rejection_reason: str = "",
    ) -> RoleUpgradeRequest:
        """Keur een aanvraag goed of wijs deze af."""

        reviewer = self._get_active_user(reviewer_id)
        if reviewer.role.name != UserService.ADMINISTRATOR_ROLE_NAME:
            raise AuthorizationError(
                "Alleen een beheerder mag rolverhogingsaanvragen beoordelen.",
                code="ADMINISTRATOR_REQUIRED",
            )

        request_item = self.repository.get(request_id)
        if request_item is None:
            raise ValidationError(
                "Rolverhogingsaanvraag niet gevonden.",
                code="ROLE_UPGRADE_REQUEST_NOT_FOUND",
            )
        if request_item.status != self.PENDING:
            raise ValidationError(
                "Deze rolverhogingsaanvraag is al beoordeeld.",
                code="ROLE_UPGRADE_ALREADY_REVIEWED",
            )

        user = request_item.user
        expected_role = self.ROLE_SEQUENCE.get(user.role.name)
        if approve and expected_role != request_item.requested_role:
            raise ValidationError(
                "De huidige gebruikersrol past niet meer bij deze aanvraag.",
                code="ROLE_UPGRADE_STALE",
            )

        reason = rejection_reason.strip() or None
        if approve:
            UserService(repository=self.user_repository).update_user(
                user.id,
                username=user.username,
                role_name=request_item.requested_role,
                is_active=user.is_active,
                acting_user_id=reviewer.id,
            )
            status = self.APPROVED
            reason = None
        else:
            status = self.REJECTED

        self.repository.review(
            request_item,
            status=status,
            reviewed_by_user_id=reviewer.id,
            rejection_reason=reason,
        )
        self.repository.save()
        self._notify_applicant(request_item)
        return request_item

    def role_label(self, role_name: str) -> str:
        """Geef een Nederlandse rolnaam terug."""

        return self.ROLE_LABELS.get(role_name, role_name)

    def _get_active_user(self, user_id: int) -> User:
        user = self.user_repository.get(user_id)
        if user is None:
            raise ValidationError("Gebruiker niet gevonden.", code="USER_NOT_FOUND")
        if not user.is_active:
            raise AuthorizationError(
                "Dit gebruikersaccount is niet actief.",
                code="USER_INACTIVE",
            )
        return user

    def _notify_administrators(
        self, user: User, request_item: RoleUpgradeRequest
    ) -> None:
        """Mail actieve beheerders over een nieuwe aanvraag."""

        recipients = {
            candidate.email
            for candidate in self.user_repository.get_all()
            if (
                candidate.is_active
                and candidate.role.name == UserService.ADMINISTRATOR_ROLE_NAME
                and candidate.email
            )
        }
        if not recipients:
            return

        base_url = current_app.config["PUBLIC_BASE_URL"].rstrip("/")
        requested_label = self.role_label(request_item.requested_role)
        body = (
            f"Gebruiker {user.username} vraagt de rol {requested_label} aan.\n\n"
            f"Beoordelen: {base_url}/admin/role-requests\n"
        )
        for recipient in recipients:
            self.mail_service.send_text(
                recipient=recipient,
                subject="Nieuwe rolverhogingsaanvraag in FNO",
                body=body,
            )

    def _notify_applicant(self, request_item: RoleUpgradeRequest) -> None:
        """Mail de aanvrager over de beoordeling."""

        user = request_item.user
        if user.email is None:
            return

        requested_label = self.role_label(request_item.requested_role)
        if request_item.status == self.APPROVED:
            body = (
                f"Je aanvraag voor de rol {requested_label} is goedgekeurd.\n"
                "De nieuwe rechten zijn direct actief.\n"
            )
        else:
            body = f"Je aanvraag voor de rol {requested_label} is afgewezen.\n"
            if request_item.rejection_reason:
                body += f"Reden: {request_item.rejection_reason}\n"

        self.mail_service.send_text(
            recipient=user.email,
            subject="Beoordeling van je FNO-rolaanvraag",
            body=body,
        )
