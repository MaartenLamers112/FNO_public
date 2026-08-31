"""Tests voor CommentRepository."""

from app.enums.author_type import AuthorType
from app.enums.comment_status import CommentStatus
from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import (
    CommentRepository,
    PersonRepository,
    PhotoRepository,
)


def create_photo(
    mm_id: str = "MM-COMMENT-001",
    photo_number: str = "A20001",
) -> Photo:
    """Maak een testfoto aan."""

    repository = PhotoRepository()

    photo = Photo(
        mm_id=mm_id,
        photo_number=photo_number,
        publication_status=PublicationStatus.CONCEPT,
    )

    repository.add(photo)
    repository.save()

    return photo


def test_comment_repository_can_create_photo_comment(app) -> None:
    """Een foto-opmerking kan worden opgeslagen en opgehaald."""

    photo = create_photo()
    repository = CommentRepository()

    comment = repository.create(
        photo_id=photo.id,
        content="Dit is een foto-opmerking.",
        author_type=AuthorType.VISITOR,
    )
    repository.save()

    comments = repository.get_by_photo(photo.id)

    assert len(comments) == 1
    assert comments[0].id == comment.id
    assert comments[0].person_id is None
    assert comments[0].status == CommentStatus.OPEN


def test_comment_repository_can_create_person_comment(app) -> None:
    """Een opmerking kan aan een persoon worden gekoppeld."""

    photo = create_photo()
    person_repository = PersonRepository()
    comment_repository = CommentRepository()

    person = person_repository.create(
        photo_id=photo.id,
        label_number=1,
        x_position=0.25,
        y_position=0.50,
    )
    person_repository.save()

    comment_repository.create(
        photo_id=photo.id,
        person_id=person.id,
        content="Mogelijk is dit Jan Peters.",
        author_type=AuthorType.VISITOR,
    )
    comment_repository.save()

    comments = comment_repository.get_by_person(person.id)

    assert len(comments) == 1
    assert comments[0].photo_id == photo.id
    assert comments[0].person_id == person.id


def test_comment_repository_can_get_open_comments(app) -> None:
    """Alleen open opmerkingen worden door de open selectie teruggegeven."""

    photo = create_photo()
    repository = CommentRepository()

    repository.create(
        photo_id=photo.id,
        content="Open opmerking",
        author_type=AuthorType.VISITOR,
    )

    closed_comment = repository.create(
        photo_id=photo.id,
        content="Gesloten opmerking",
        author_type=AuthorType.EMPLOYEE,
    )

    repository.change_status(
        closed_comment,
        status=CommentStatus.CLOSED,
    )
    repository.save()

    comments = repository.get_open_by_photo(photo.id)

    assert len(comments) == 1
    assert comments[0].content == "Open opmerking"
    assert repository.count_open_by_photo(photo.id) == 1


def test_comment_repository_can_change_and_reopen_status(app) -> None:
    """Sluiten en opnieuw openen beheert ook de sluitingsvelden."""

    photo = create_photo()
    repository = CommentRepository()

    comment = repository.create(
        photo_id=photo.id,
        content="Te beoordelen",
        author_type=AuthorType.EMPLOYEE,
    )
    repository.save()

    repository.change_status(
        comment,
        status=CommentStatus.RESOLVED,
        closed_by_user_id=None,
    )
    repository.save()

    assert comment.status == CommentStatus.RESOLVED
    assert comment.closed_at is not None

    repository.change_status(
        comment,
        status=CommentStatus.OPEN,
    )
    repository.save()

    assert comment.status == CommentStatus.OPEN
    assert comment.closed_at is None
    assert comment.closed_by_user_id is None


def test_comment_repository_can_update_content(app) -> None:
    """De inhoud van een opmerking kan worden gecorrigeerd."""

    photo = create_photo()
    repository = CommentRepository()

    comment = repository.create(
        photo_id=photo.id,
        content="Oude tekst",
        author_type=AuthorType.EMPLOYEE,
    )
    repository.save()

    repository.update_content(
        comment,
        content="Nieuwe tekst",
    )
    repository.save()

    stored_comment = repository.get(comment.id)

    assert stored_comment is not None
    assert stored_comment.content == "Nieuwe tekst"


def test_deleted_comment_is_hidden_by_default(app) -> None:
    """Administratief verwijderde opmerkingen zijn standaard onzichtbaar."""

    photo = create_photo()
    repository = CommentRepository()

    comment = repository.create(
        photo_id=photo.id,
        content="Te verwijderen",
        author_type=AuthorType.ADMINISTRATOR,
    )
    repository.save()

    repository.mark_deleted(comment)
    repository.save()

    assert repository.get_by_photo(photo.id) == []

    comments = repository.get_by_photo(
        photo.id,
        include_deleted=True,
    )

    assert len(comments) == 1
    assert comments[0].is_deleted is True
    assert comments[0].deleted_at is not None


def test_comment_repository_can_search_and_count_status(app) -> None:
    """Opmerkingen kunnen op status worden geselecteerd en geteld."""

    first_photo = create_photo()
    second_photo = create_photo(
        mm_id="MM-COMMENT-002",
        photo_number="A20002",
    )
    repository = CommentRepository()

    repository.create(
        photo_id=first_photo.id,
        content="Eerste open opmerking",
        author_type=AuthorType.VISITOR,
    )
    repository.create(
        photo_id=second_photo.id,
        content="Tweede open opmerking",
        author_type=AuthorType.VISITOR,
    )

    resolved_comment = repository.create(
        photo_id=second_photo.id,
        content="Afgehandelde opmerking",
        author_type=AuthorType.EMPLOYEE,
    )
    repository.change_status(
        resolved_comment,
        status=CommentStatus.RESOLVED,
    )
    repository.save()

    open_comments = repository.search_by_status(CommentStatus.OPEN)

    assert len(open_comments) == 2
    assert repository.count_open() == 2
