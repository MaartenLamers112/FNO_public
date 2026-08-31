"""Repository voor opmerkingen bij foto's en personen."""

from __future__ import annotations

from sqlalchemy import func, select

from app.enums.comment_status import CommentStatus
from app.extensions import db
from app.models import Comment
from app.models.mixins import utc_now
from app.repositories.base_repository import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    """Databasebewerkingen voor de Comment-entiteit."""

    model = Comment

    def get_by_photo(
        self,
        photo_id: int,
        *,
        include_deleted: bool = False,
    ) -> list[Comment]:
        """Geef opmerkingen van een foto terug."""

        statement = select(Comment).where(Comment.photo_id == photo_id)

        if not include_deleted:
            statement = statement.where(Comment.is_deleted.is_(False))

        statement = statement.order_by(Comment.created_at)

        return list(db.session.scalars(statement))

    def get_by_person(
        self,
        person_id: int,
        *,
        include_deleted: bool = False,
    ) -> list[Comment]:
        """Geef opmerkingen van een persoon terug."""

        statement = select(Comment).where(Comment.person_id == person_id)

        if not include_deleted:
            statement = statement.where(Comment.is_deleted.is_(False))

        statement = statement.order_by(Comment.created_at)

        return list(db.session.scalars(statement))

    def get_open_by_photo(
        self,
        photo_id: int,
    ) -> list[Comment]:
        """Geef alle open, niet-verwijderde opmerkingen van een foto."""

        statement = (
            select(Comment)
            .where(
                Comment.photo_id == photo_id,
                Comment.status == CommentStatus.OPEN,
                Comment.is_deleted.is_(False),
            )
            .order_by(Comment.created_at)
        )

        return list(db.session.scalars(statement))

    def search_by_status(
        self,
        status: CommentStatus | str,
    ) -> list[Comment]:
        """Geef niet-verwijderde opmerkingen met een bepaalde status."""

        statement = (
            select(Comment)
            .where(
                Comment.status == str(status),
                Comment.is_deleted.is_(False),
            )
            .order_by(
                Comment.photo_id,
                Comment.created_at,
            )
        )

        return list(db.session.scalars(statement))

    def create(
        self,
        *,
        photo_id: int,
        content: str,
        author_type: str,
        person_id: int | None = None,
        user_id: int | None = None,
        status: CommentStatus | str = CommentStatus.OPEN,
    ) -> Comment:
        """Maak een nieuwe opmerking aan."""

        comment = Comment(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            author_type=author_type,
            content=content,
            status=str(status),
        )

        return self.add(comment)

    def update_content(
        self,
        comment: Comment,
        *,
        content: str,
    ) -> Comment:
        """Wijzig de inhoud van een opmerking."""

        comment.content = content

        return comment

    def change_status(
        self,
        comment: Comment,
        *,
        status: CommentStatus | str,
        closed_by_user_id: int | None = None,
    ) -> Comment:
        """Wijzig de status van een opmerking."""

        normalized_status = str(status)
        comment.status = normalized_status

        if normalized_status in {
            CommentStatus.RESOLVED,
            CommentStatus.CLOSED,
        }:
            comment.closed_at = utc_now()
            comment.closed_by_user_id = closed_by_user_id
        else:
            comment.closed_at = None
            comment.closed_by_user_id = None

        return comment

    def mark_deleted(
        self,
        comment: Comment,
        *,
        deleted_by_user_id: int | None = None,
    ) -> Comment:
        """Markeer een opmerking als administratief verwijderd."""

        comment.is_deleted = True
        comment.deleted_at = utc_now()
        comment.deleted_by_user_id = deleted_by_user_id

        return comment

    def count_open(self) -> int:
        """Tel alle open, niet-verwijderde opmerkingen."""

        statement = (
            select(func.count())
            .select_from(Comment)
            .where(
                Comment.status == CommentStatus.OPEN,
                Comment.is_deleted.is_(False),
            )
        )

        return db.session.scalar(statement) or 0

    def count_open_by_photo(
        self,
        photo_id: int,
    ) -> int:
        """Tel open, niet-verwijderde opmerkingen van één foto."""

        statement = (
            select(func.count())
            .select_from(Comment)
            .where(
                Comment.photo_id == photo_id,
                Comment.status == CommentStatus.OPEN,
                Comment.is_deleted.is_(False),
            )
        )

        return db.session.scalar(statement) or 0
