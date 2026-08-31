"""Decorators voor centrale autorisatiecontroles."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from app.services.authorization_service import AuthorizationService


def employee_required[F: Callable[..., Any]](view: F) -> F:
    """Vereis een medewerker of beheerder voor de endpoint."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        AuthorizationService().require_label_management()
        return view(*args, **kwargs)

    return cast(F, wrapped)


def admin_required[F: Callable[..., Any]](view: F) -> F:
    """Vereis een beheerder voor de endpoint."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        AuthorizationService().require_administrator()
        return view(*args, **kwargs)

    return cast(F, wrapped)


def publication_management_required[F: Callable[..., Any]](view: F) -> F:
    """Vereis een beheerder voor het wijzigen van publicatiestatus."""

    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        AuthorizationService().require_publication_management()
        return view(*args, **kwargs)

    return cast(F, wrapped)
