"""Tests voor CommentService."""

import pytest

from app.enums.author_type import AuthorType
from app.enums.comment_status import CommentStatus
from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.exceptions import NotFoundError, ValidationError
from app.models import Photo
from app.repositories import (
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
    RoleRepository,
    UserRepository,
)
from app.services import CommentService


def create_photo(
    *,
    mm_id: str = "MM-COMMENT-SERVICE-001",
    photo_number: str = "A80001",
) -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()

    photo = repository.add(
        Photo(
            mm_id=mm_id,
            photo_number=photo_number,
            publication_status=PublicationStatus.CONCEPT,
        )
    )
    repository.save()

    return photo


def create_user() -> int:
    """Maak een testmedewerker aan."""

    role_repository = RoleRepository()
    user_repository = UserRepository()

    role = role_repository.create(
        name="employee",
        description="Medewerker",
    )
    role_repository.save()

    user = user_repository.create(
        username="medewerker",
        password_hash="test-hash",
        role_id=role.id,
    )
    user_repository.save()

    return user.id


def test_visitor_can_create_photo_comment(app) -> None:
    """Een bezoeker kan een opmerking bij een foto plaatsen."""

    photo = create_photo()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="  Wie herkent deze personen?  ",
        author_type=AuthorType.VISITOR,
    )

    assert comment.id is not None
    assert comment.photo_id == photo.id
    assert comment.person_id is None
    assert comment.user_id is None
    assert comment.author_type == AuthorType.VISITOR
    assert comment.content == "Wie herkent deze personen?"


def test_visitor_can_create_person_comment(app) -> None:
    """Een bezoeker kan een opmerking bij een persoon plaatsen."""

    photo = create_photo()
    person_repository = PersonRepository()

    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
    )
    person_repository.save()

    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        person_id=person.id,
        content="Volgens mij is dit Jan Peters.",
        author_type=AuthorType.VISITOR,
    )

    assert comment.person_id == person.id


def test_comment_requires_existing_photo(app) -> None:
    """Een opmerking vereist een bestaande foto."""

    service = CommentService()

    with pytest.raises(NotFoundError) as exc:
        service.create_comment(
            photo_id=999999,
            content="Test",
            author_type=AuthorType.VISITOR,
        )

    assert exc.value.code == "PHOTO_NOT_FOUND"
    assert exc.value.details == {
        "photo_id": 999999,
    }


def test_comment_requires_existing_person(app) -> None:
    """Een persoonsopmerking vereist een bestaand label."""

    photo = create_photo()
    service = CommentService()

    with pytest.raises(NotFoundError) as exc:
        service.create_comment(
            photo_id=photo.id,
            person_id=999999,
            content="Test",
            author_type=AuthorType.VISITOR,
        )

    assert exc.value.code == "PERSON_NOT_FOUND"
    assert exc.value.details == {
        "person_id": 999999,
    }


def test_person_must_belong_to_comment_photo(app) -> None:
    """Het gekozen label moet bij dezelfde foto horen."""

    first_photo = create_photo()
    second_photo = create_photo(
        mm_id="MM-COMMENT-SERVICE-002",
        photo_number="A80002",
    )

    person_repository = PersonRepository()

    person = person_repository.create(
        photo_id=first_photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
    )
    person_repository.save()

    service = CommentService()

    with pytest.raises(ValidationError) as exc:
        service.create_comment(
            photo_id=second_photo.id,
            person_id=person.id,
            content="Test",
            author_type=AuthorType.VISITOR,
        )

    assert exc.value.code == "PERSON_PHOTO_MISMATCH"
    assert exc.value.details == {
        "person_id": person.id,
        "person_photo_id": first_photo.id,
        "photo_id": second_photo.id,
    }


def test_comment_content_is_required(app) -> None:
    """Een lege opmerking wordt geweigerd."""

    photo = create_photo()
    service = CommentService()

    with pytest.raises(ValidationError) as exc:
        service.create_comment(
            photo_id=photo.id,
            content="   ",
            author_type=AuthorType.VISITOR,
        )

    assert exc.value.code == "COMMENT_CONTENT_REQUIRED"
    assert exc.value.details == {}


def test_visitor_comment_cannot_contain_user(app) -> None:
    """Een bezoekersopmerking mag niet aan een gebruiker hangen."""

    photo = create_photo()
    service = CommentService()

    with pytest.raises(ValidationError) as exc:
        service.create_comment(
            photo_id=photo.id,
            content="Test",
            author_type=AuthorType.VISITOR,
            user_id=123,
        )

    assert exc.value.code == "COMMENT_VISITOR_USER_NOT_ALLOWED"
    assert exc.value.details == {
        "user_id": 123,
    }


@pytest.mark.parametrize(
    "author_type",
    [
        AuthorType.EMPLOYEE,
        AuthorType.ADMINISTRATOR,
    ],
)
def test_authenticated_author_requires_user(
    app,
    author_type: AuthorType,
) -> None:
    """Medewerkers en beheerders vereisen een gebruikers-ID."""

    photo = create_photo()
    service = CommentService()

    with pytest.raises(ValidationError) as exc:
        service.create_comment(
            photo_id=photo.id,
            content="Interne opmerking",
            author_type=author_type,
        )

    assert exc.value.code == "COMMENT_USER_REQUIRED"
    assert exc.value.details == {
        "author_type": author_type.value,
    }


def test_create_comment_writes_history(app) -> None:
    """Het plaatsen van een opmerking schrijft historie."""

    photo = create_photo()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Wie is dit?",
        author_type=AuthorType.VISITOR,
    )

    history = HistoryRepository().get_by_photo(photo.id)

    created_events = [
        item for item in history if item.event_type == HistoryEventType.COMMENT_CREATED
    ]

    assert len(created_events) == 1
    assert created_events[0].description == (
        f"Opmerking {comment.id} toegevoegd aan foto"
    )
    assert created_events[0].new_value == "Wie is dit?"


def test_comment_can_be_resolved(app) -> None:
    """Een open opmerking kan worden afgehandeld."""

    photo = create_photo()
    user_id = create_user()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Controleer deze naam.",
        author_type=AuthorType.VISITOR,
    )

    resolved = service.resolve_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    assert resolved.status == CommentStatus.RESOLVED
    assert resolved.closed_at is not None
    assert resolved.closed_by_user_id == user_id


def test_comment_can_be_closed(app) -> None:
    """Een open opmerking kan worden gesloten."""

    photo = create_photo()
    user_id = create_user()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Geen verdere actie nodig.",
        author_type=AuthorType.VISITOR,
    )

    closed = service.close_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    assert closed.status == CommentStatus.CLOSED
    assert closed.closed_at is not None
    assert closed.closed_by_user_id == user_id


def test_comment_can_be_reopened(app) -> None:
    """Een gesloten opmerking kan opnieuw worden geopend."""

    photo = create_photo()
    user_id = create_user()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Nogmaals controleren.",
        author_type=AuthorType.VISITOR,
    )

    service.close_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    reopened = service.reopen_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    assert reopened.status == CommentStatus.OPEN
    assert reopened.closed_at is None
    assert reopened.closed_by_user_id is None


def test_same_comment_status_does_nothing(app) -> None:
    """Dezelfde status opnieuw instellen schrijft geen historie."""

    photo = create_photo()
    user_id = create_user()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Test",
        author_type=AuthorType.VISITOR,
    )

    history_before = len(HistoryRepository().get_by_photo(photo.id))

    service.reopen_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    history_after = len(HistoryRepository().get_by_photo(photo.id))

    assert history_after == history_before


def test_unknown_comment_status_change_fails(app) -> None:
    """Een onbekende opmerking kan niet worden gewijzigd."""

    service = CommentService()

    with pytest.raises(NotFoundError) as exc:
        service.close_comment(
            comment_id=999999,
            user_id=1,
        )

    assert exc.value.code == "COMMENT_NOT_FOUND"
    assert exc.value.details == {
        "comment_id": 999999,
    }


def test_comment_status_change_writes_history(app) -> None:
    """Een statuswijziging wordt in de historie geregistreerd."""

    photo = create_photo()
    user_id = create_user()
    service = CommentService()

    comment = service.create_comment(
        photo_id=photo.id,
        content="Te controleren.",
        author_type=AuthorType.VISITOR,
    )

    service.resolve_comment(
        comment_id=comment.id,
        user_id=user_id,
    )

    history = HistoryRepository().get_by_photo(photo.id)

    resolved_events = [
        item for item in history if item.event_type == HistoryEventType.COMMENT_RESOLVED
    ]

    assert len(resolved_events) == 1
    assert resolved_events[0].user_id == user_id
    assert resolved_events[0].old_value == "open"
    assert resolved_events[0].new_value == "resolved"


def test_comment_can_be_deleted(app) -> None:
    """Een verwijderde opmerking verdwijnt uit de normale resultaten."""

    photo = create_photo()
    service = CommentService()
    comment = service.create_comment(
        photo_id=photo.id,
        content="Tijdelijke opmerking",
        author_type=AuthorType.VISITOR,
    )

    service.delete_comment(comment_id=comment.id)

    assert service.get_by_photo(photo.id) == []
    stored = service.get(comment.id)
    assert stored is not None
    assert stored.is_deleted is True

    events = HistoryRepository().get_by_photo(photo.id)
    assert any(event.event_type == HistoryEventType.COMMENT_DELETED for event in events)


def test_person_comment_text_is_consolidated(app) -> None:
    """Meerdere opmerkingen worden als één doorlopende tekst opgeslagen."""

    photo = create_photo()
    from app.repositories import PersonRepository

    person = PersonRepository().create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
    )
    PersonRepository().save()
    service = CommentService()
    service.create_comment(
        photo_id=photo.id,
        person_id=person.id,
        content="Eerste opmerking",
        author_type=AuthorType.VISITOR,
    )
    service.create_comment(
        photo_id=photo.id,
        person_id=person.id,
        content="Tweede opmerking",
        author_type=AuthorType.VISITOR,
    )

    content = service.set_person_comment_text(
        person_id=person.id,
        content="Eerste opmerking\n\nTweede opmerking\nNieuwe regel",
    )

    comments = service.get_by_person(person.id)
    assert content == "Eerste opmerking\n\nTweede opmerking\nNieuwe regel"
    assert len(comments) == 1
    assert comments[0].content == content


def test_empty_person_comment_text_removes_comments(app) -> None:
    """Een leeggemaakt opmerkingenveld verwijdert de actuele tekst."""

    photo = create_photo()
    from app.repositories import PersonRepository

    person = PersonRepository().create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.2,
        y_position=0.3,
    )
    PersonRepository().save()
    service = CommentService()
    service.create_comment(
        photo_id=photo.id,
        person_id=person.id,
        content="Tijdelijke opmerking",
        author_type=AuthorType.VISITOR,
    )

    content = service.set_person_comment_text(person_id=person.id, content="   ")

    assert content == ""
    assert service.get_by_person(person.id) == []


def test_create_person_comment_resolves_photo_in_service(app) -> None:
    """De service bepaalt zelf bij welke foto een persoonsopmerking hoort."""

    photo = create_photo()
    person_repository = PersonRepository()
    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
    )
    person_repository.save()

    comment = CommentService().create_person_comment(
        person_id=person.id,
        content="Aanvullende informatie.",
        author_type=AuthorType.VISITOR,
    )

    assert comment.photo_id == photo.id
    assert comment.person_id == person.id
    assert comment.content == "Aanvullende informatie."
