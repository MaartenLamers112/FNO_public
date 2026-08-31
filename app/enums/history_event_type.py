"""Ondersteunde gebeurtenistypen voor de algemene historie."""

from enum import StrEnum


class HistoryEventType(StrEnum):
    """Gebeurtenistypen volgens het Software Technical Design."""

    LABEL_CREATED = "label_created"
    LABEL_DELETED = "label_deleted"
    LABEL_MOVED = "label_moved"
    LABEL_RENUMBERED = "label_renumbered"

    NAME_CREATED = "name_created"
    NAME_CHANGED = "name_changed"
    NAME_CLEARED = "name_cleared"
    NAME_LOCKED = "name_locked"
    NAME_UNLOCKED = "name_unlocked"

    METADATA_CHANGED = "metadata_changed"

    COMMENT_CREATED = "comment_created"
    COMMENT_CHANGED = "comment_changed"
    COMMENT_RESOLVED = "comment_resolved"
    COMMENT_CLOSED = "comment_closed"
    COMMENT_REOPENED = "comment_reopened"
    COMMENT_DELETED = "comment_deleted"

    PHOTO_PUBLISHED = "photo_published"
    PHOTO_HIDDEN = "photo_hidden"
    PHOTO_CONCEPT = "photo_concept"
    PHOTO_IMPORTED = "photo_imported"
    PHOTO_VISIBILITY_CHANGED = "photo_visibility_changed"
    PHOTO_COMPLETION_CHANGED = "photo_completion_changed"
    PHOTO_PERSON_DISPLAY_MODE_CHANGED = "photo_person_display_mode_changed"
    PHOTO_LABEL_SIZE_CHANGED = "photo_label_size_changed"

    SYNCHRONIZATION_STARTED = "synchronization_started"
    SYNCHRONIZATION_COMPLETED = "synchronization_completed"
    SYNCHRONIZATION_FAILED = "synchronization_failed"

    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
