from app.enums.publication_status import PublicationStatus
from app.models import Photo
from app.repositories import PhotoRepository


def create_photo(
    mm_id: str,
    number: str,
    status: PublicationStatus,
) -> Photo:
    repo = PhotoRepository()

    photo = Photo(
        mm_id=mm_id,
        photo_number=number,
        publication_status=status,
    )

    repo.add(photo)
    repo.save()

    return photo


def test_find_by_mm_id(app):
    create_photo(
        "MM1",
        "A00001",
        PublicationStatus.CONCEPT,
    )

    repo = PhotoRepository()

    photo = repo.get_by_mm_id("MM1")

    assert photo is not None
    assert photo.photo_number == "A00001"


def test_find_by_photo_number(app):
    create_photo(
        "MM2",
        "A00002",
        PublicationStatus.CONCEPT,
    )

    repo = PhotoRepository()

    photo = repo.get_by_photo_number("A00002")

    assert photo is not None
    assert photo.mm_id == "MM2"


def test_get_next_and_previous(app):
    create_photo(
        "MM1",
        "A00001",
        PublicationStatus.CONCEPT,
    )

    create_photo(
        "MM2",
        "A00002",
        PublicationStatus.CONCEPT,
    )

    create_photo(
        "MM3",
        "A00003",
        PublicationStatus.CONCEPT,
    )

    repo = PhotoRepository()

    assert repo.get_previous("A00002").photo_number == "A00001"

    assert repo.get_next("A00002").photo_number == "A00003"


def test_get_published(app):
    create_photo(
        "MM1",
        "A00001",
        PublicationStatus.CONCEPT,
    )

    create_photo(
        "MM2",
        "A00002",
        PublicationStatus.PUBLISHED,
    )

    repo = PhotoRepository()

    photos = repo.get_published()

    assert len(photos) == 1
    assert photos[0].photo_number == "A00002"


def test_get_by_mm_ids_returns_matching_photos(app):
    """Meerdere MM-id's worden in één repositoryaanroep opgehaald."""

    create_photo("MM1", "A00001", PublicationStatus.CONCEPT)
    create_photo("MM2", "A00002", PublicationStatus.CONCEPT)
    create_photo("MM3", "A00003", PublicationStatus.CONCEPT)

    photos = PhotoRepository().get_by_mm_ids({"MM1", "MM3", "UNKNOWN"})

    assert {photo.mm_id for photo in photos} == {"MM1", "MM3"}
