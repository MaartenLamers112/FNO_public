"""Bedrijfslogica voor opmerkingen."""

from __future__ import annotations

from app.enums.author_type import AuthorType
from app.enums.comment_status import CommentStatus
from app.enums.history_event_type import HistoryEventType
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Comment, Person, Photo
from app.repositories import (
    CommentRepository,
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
)
from app.services.base_service import BaseService


class CommentService(BaseService[CommentRepository]):
    """Bedrijfslogica rondom opmerkingen."""

    def __init__(
        self,
        repository: CommentRepository | None = None,
        *,
        photo_repository: PhotoRepository | None = None,
        person_repository: PersonRepository | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        """Initialiseer de service en zijn repositoryafhankelijkheden."""

        super().__init__(repository or CommentRepository())

        self.photo_repository = photo_repository or PhotoRepository()
        self.person_repository = person_repository or PersonRepository()
        self.history_repository = history_repository or HistoryRepository()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def get(
        self,
        comment_id: int,
    ) -> Comment | None:
        """Haal een opmerking op via de primaire sleutel."""

        return self.repository.get(comment_id)

    def create_comment(
        self,
        *,
        photo_id: int,
        content: str,
        author_type: AuthorType,
        person_id: int | None = None,
        user_id: int | None = None,
    ) -> Comment:
        """Maak een nieuwe opmerking bij een foto of persoon."""

        self._get_required_photo(photo_id)

        person = None

        if person_id is not None:
            person = self._get_required_person(person_id)
            self._validate_person_photo(
                person=person,
                photo_id=photo_id,
            )

        normalized_content = self._normalize_content(content)

        self._validate_author(
            author_type=author_type,
            user_id=user_id,
        )

        comment = self.repository.create(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            author_type=author_type,
            content=normalized_content,
        )

        self.repository.flush()

        self.history_repository.create(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            event_type=HistoryEventType.COMMENT_CREATED,
            description=self._create_history_description(
                comment=comment,
                person=person,
            ),
            new_value=normalized_content,
        )

        self._commit()

        return comment

    def get_by_person(
        self,
        person_id: int,
    ) -> list[Comment]:
        """Geef alle opmerkingen van een persoon."""

        self._get_required_person(person_id)
        return self.repository.get_by_person(person_id)

    def create_person_comment(
        self,
        *,
        person_id: int,
        content: str,
        author_type: AuthorType,
        user_id: int | None = None,
    ) -> Comment:
        """Maak een nieuwe opmerking bij een bestaande persoon."""

        person = self._get_required_person(person_id)
        return self.create_comment(
            photo_id=person.photo_id,
            person_id=person_id,
            content=content,
            author_type=author_type,
            user_id=user_id,
        )

    def update_comment(
        self,
        *,
        comment_id: int,
        content: str,
        user_id: int | None = None,
    ) -> Comment:
        """Wijzig de inhoud van een opmerking."""

        comment = self._get_required_comment(comment_id)
        normalized_content = self._normalize_content(content)
        old_content = comment.content

        if old_content == normalized_content:
            return comment

        self.repository.update_content(comment, content=normalized_content)
        self.history_repository.create(
            photo_id=comment.photo_id,
            person_id=comment.person_id,
            user_id=user_id,
            event_type=HistoryEventType.COMMENT_CHANGED,
            description="Opmerking gewijzigd",
            old_value=old_content,
            new_value=normalized_content,
        )
        self._commit()
        return comment

    def set_person_comment_text(
        self,
        *,
        person_id: int,
        content: str,
        user_id: int | None = None,
    ) -> str:
        """Sla één doorlopende opmerkingstekst voor een persoon op."""

        person = self._get_required_person(person_id)
        normalized_content = content.strip()
        comments = self.repository.get_by_person(person_id)

        if not normalized_content:
            for comment in comments:
                self.repository.mark_deleted(
                    comment,
                    deleted_by_user_id=user_id,
                )
                self.history_repository.create(
                    photo_id=comment.photo_id,
                    person_id=person_id,
                    user_id=user_id,
                    event_type=HistoryEventType.COMMENT_DELETED,
                    description="Opmerking verwijderd",
                    old_value=comment.content,
                )

            if comments:
                self._commit()
            return ""

        if not comments:
            comment = self.repository.create(
                photo_id=person.photo_id,
                person_id=person_id,
                user_id=user_id,
                author_type=AuthorType.VISITOR,
                content=normalized_content,
            )
            self.repository.flush()
            self.history_repository.create(
                photo_id=person.photo_id,
                person_id=person_id,
                user_id=user_id,
                event_type=HistoryEventType.COMMENT_CREATED,
                description=f"Opmerking toegevoegd aan label {person.label_number}",
                new_value=normalized_content,
            )
            self._commit()
            return comment.content

        primary = comments[0]
        old_content = "\n\n".join(comment.content for comment in comments)
        if primary.content != normalized_content:
            self.repository.update_content(primary, content=normalized_content)
            self.history_repository.create(
                photo_id=primary.photo_id,
                person_id=person_id,
                user_id=user_id,
                event_type=HistoryEventType.COMMENT_CHANGED,
                description="Opmerking gewijzigd",
                old_value=old_content,
                new_value=normalized_content,
            )

        for comment in comments[1:]:
            self.repository.mark_deleted(
                comment,
                deleted_by_user_id=user_id,
            )

        self._commit()
        return normalized_content

    def delete_comment(
        self,
        *,
        comment_id: int,
        user_id: int | None = None,
    ) -> None:
        """Markeer een opmerking als verwijderd en schrijf historie."""

        comment = self._get_required_comment(comment_id)
        if comment.is_deleted:
            return

        self.repository.mark_deleted(
            comment,
            deleted_by_user_id=user_id,
        )
        self.history_repository.create(
            photo_id=comment.photo_id,
            person_id=comment.person_id,
            user_id=user_id,
            event_type=HistoryEventType.COMMENT_DELETED,
            description="Opmerking verwijderd",
            old_value=comment.content,
        )
        self._commit()

    def resolve_comment(
        self,
        *,
        comment_id: int,
        user_id: int,
    ) -> Comment:
        """Markeer een opmerking als afgehandeld."""

        return self._change_status(
            comment_id=comment_id,
            new_status=CommentStatus.RESOLVED,
            event_type=HistoryEventType.COMMENT_RESOLVED,
            description="Opmerking afgehandeld",
            user_id=user_id,
        )

    def close_comment(
        self,
        *,
        comment_id: int,
        user_id: int,
    ) -> Comment:
        """Sluit een opmerking."""

        return self._change_status(
            comment_id=comment_id,
            new_status=CommentStatus.CLOSED,
            event_type=HistoryEventType.COMMENT_CLOSED,
            description="Opmerking gesloten",
            user_id=user_id,
        )

    def reopen_comment(
        self,
        *,
        comment_id: int,
        user_id: int,
    ) -> Comment:
        """Heropen een eerder afgehandelde of gesloten opmerking."""

        return self._change_status(
            comment_id=comment_id,
            new_status=CommentStatus.OPEN,
            event_type=HistoryEventType.COMMENT_REOPENED,
            description="Opmerking heropend",
            user_id=user_id,
        )

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------

    def _get_required_photo(
        self,
        photo_id: int,
    ) -> Photo:
        """Haal een foto op of meld dat deze niet bestaat."""

        photo = self.photo_repository.get(photo_id)

        if photo is None:
            raise NotFoundError(
                "De foto bestaat niet.",
                code="PHOTO_NOT_FOUND",
                details={
                    "photo_id": photo_id,
                },
            )

        return photo

    def _get_required_person(
        self,
        person_id: int,
    ) -> Person:
        """Haal een persoon op of meld dat deze niet bestaat."""

        person = self.person_repository.get(person_id)

        if person is None:
            raise NotFoundError(
                "Het label bestaat niet.",
                code="PERSON_NOT_FOUND",
                details={
                    "person_id": person_id,
                },
            )

        return person

    @staticmethod
    def _validate_person_photo(
        *,
        person: Person,
        photo_id: int,
    ) -> None:
        """Controleer of de persoon bij de opgegeven foto hoort."""

        if person.photo_id != photo_id:
            raise ValidationError(
                "Het label hoort niet bij de opgegeven foto.",
                code="PERSON_PHOTO_MISMATCH",
                details={
                    "person_id": person.id,
                    "person_photo_id": person.photo_id,
                    "photo_id": photo_id,
                },
            )

    @staticmethod
    def _normalize_content(
        content: str,
    ) -> str:
        """Normaliseer en valideer de inhoud van een opmerking."""

        normalized_content = content.strip()

        if not normalized_content:
            raise ValidationError(
                "De opmerking mag niet leeg zijn.",
                code="COMMENT_CONTENT_REQUIRED",
            )

        return normalized_content

    @staticmethod
    def _validate_author(
        *,
        author_type: AuthorType,
        user_id: int | None,
    ) -> None:
        """Controleer de combinatie van auteurstype en gebruiker."""

        if author_type == AuthorType.VISITOR:
            if user_id is not None:
                raise ValidationError(
                    "Een bezoekersopmerking mag geen gebruiker bevatten.",
                    code="COMMENT_VISITOR_USER_NOT_ALLOWED",
                    details={
                        "user_id": user_id,
                    },
                )

            return

        if (
            author_type
            in {
                AuthorType.EMPLOYEE,
                AuthorType.ADMINISTRATOR,
            }
            and user_id is None
        ):
            raise ValidationError(
                "Voor dit auteurstype is een gebruiker verplicht.",
                code="COMMENT_USER_REQUIRED",
                details={
                    "author_type": author_type.value,
                },
            )

    @staticmethod
    def _create_history_description(
        *,
        comment: Comment,
        person: Person | None,
    ) -> str:
        """Maak een leesbare omschrijving voor de historie."""

        if person is not None:
            return f"Opmerking toegevoegd aan label {person.label_number}"

        return f"Opmerking {comment.id} toegevoegd aan foto"

    def _get_required_comment(
        self,
        comment_id: int,
    ) -> Comment:
        """Haal een opmerking op of meld dat deze niet bestaat."""

        comment = self.repository.get(comment_id)

        if comment is None:
            raise NotFoundError(
                "De opmerking bestaat niet.",
                code="COMMENT_NOT_FOUND",
                details={
                    "comment_id": comment_id,
                },
            )

        return comment

    def _change_status(
        self,
        *,
        comment_id: int,
        new_status: CommentStatus,
        event_type: HistoryEventType,
        description: str,
        user_id: int,
    ) -> Comment:
        """Wijzig de status en registreer de gebeurtenis."""

        comment = self._get_required_comment(comment_id)

        if comment.is_deleted:
            raise ConflictError(
                "Een verwijderde opmerking kan niet worden gewijzigd.",
                code="COMMENT_DELETED",
                details={
                    "comment_id": comment_id,
                },
            )

        old_status = CommentStatus(comment.status)

        if old_status == new_status:
            return comment

        self.repository.change_status(
            comment,
            status=new_status,
            closed_by_user_id=(None if new_status == CommentStatus.OPEN else user_id),
        )

        self.history_repository.create(
            photo_id=comment.photo_id,
            person_id=comment.person_id,
            user_id=user_id,
            event_type=event_type,
            description=description,
            old_value=old_status.value,
            new_value=new_status.value,
        )

        self._commit()

        return comment

    def get_by_photo(
        self,
        photo_id: int,
    ) -> list[Comment]:
        """Geef alle opmerkingen van een foto."""

        self._get_required_photo(photo_id)

        return self.repository.get_by_photo(photo_id)
