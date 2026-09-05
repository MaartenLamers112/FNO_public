"""Tests voor rolverhogingsaanvragen."""

import pytest

from app.exceptions import ValidationError
from app.repositories import RoleUpgradeRequestRepository
from app.services import RoleUpgradeRequestService, UserService


def create_verified_user(*, username: str, email: str, role_name: str):
    """Maak een actieve gebruiker met bevestigd e-mailadres."""

    user = UserService().create_user(
        username=username,
        email=email,
        password="veiligwachtwoord",
        role_name=role_name,
    )
    user.email_verified = True
    RoleUpgradeRequestRepository().save()
    return user


def test_user_can_request_employee_role(app) -> None:
    """Een gebruiker kan alleen de medewerkersrol aanvragen."""

    user = create_verified_user(
        username="aanvrager",
        email="aanvrager@example.nl",
        role_name="user",
    )

    request_item = RoleUpgradeRequestService().request_upgrade(user.id)

    assert request_item.requested_role == "employee"
    assert request_item.status == "pending"


def test_employee_can_request_administrator_role(app) -> None:
    """Een medewerker kan de beheerdersrol aanvragen."""

    user = create_verified_user(
        username="medewerker",
        email="medewerker@example.nl",
        role_name="employee",
    )

    request_item = RoleUpgradeRequestService().request_upgrade(user.id)

    assert request_item.requested_role == "administrator"


def test_duplicate_pending_request_is_rejected(app) -> None:
    """Een gebruiker kan niet twee openstaande aanvragen hebben."""

    user = create_verified_user(
        username="dubbel",
        email="dubbel@example.nl",
        role_name="user",
    )
    service = RoleUpgradeRequestService()
    service.request_upgrade(user.id)

    with pytest.raises(ValidationError) as exc_info:
        service.request_upgrade(user.id)

    assert exc_info.value.code == "ROLE_UPGRADE_ALREADY_PENDING"


def test_administrator_can_approve_request(app) -> None:
    """Goedkeuren verhoogt de rol en bewaart de beoordeling."""

    applicant = create_verified_user(
        username="aanvrager",
        email="aanvrager@example.nl",
        role_name="user",
    )
    administrator = create_verified_user(
        username="beheerder",
        email="beheerder@example.nl",
        role_name="administrator",
    )
    service = RoleUpgradeRequestService()
    request_item = service.request_upgrade(applicant.id)

    reviewed = service.review_request(
        request_item.id,
        reviewer_id=administrator.id,
        approve=True,
    )

    assert reviewed.status == "approved"
    assert reviewed.reviewed_by_user_id == administrator.id
    assert reviewed.reviewed_at is not None
    assert applicant.role.name == "employee"


def test_administrator_can_reject_with_reason(app) -> None:
    """Afwijzen bewaart de optionele reden zonder de rol te wijzigen."""

    applicant = create_verified_user(
        username="aanvrager",
        email="aanvrager@example.nl",
        role_name="user",
    )
    administrator = create_verified_user(
        username="beheerder",
        email="beheerder@example.nl",
        role_name="administrator",
    )
    service = RoleUpgradeRequestService()
    request_item = service.request_upgrade(applicant.id)

    reviewed = service.review_request(
        request_item.id,
        reviewer_id=administrator.id,
        approve=False,
        rejection_reason="Eerst meer ervaring opdoen.",
    )

    assert reviewed.status == "rejected"
    assert reviewed.rejection_reason == "Eerst meer ervaring opdoen."
    assert applicant.role.name == "user"
