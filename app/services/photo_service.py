"""Bedrijfslogica voor foto's."""

from __future__ import annotations

from typing import Any

from app.enums.history_event_type import HistoryEventType
from app.enums.publication_status import PublicationStatus
from app.exceptions import ConflictError, FNOError, NotFoundError, ValidationError
from app.models import Photo
from app.repositories import (
    CommentRepository,
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
)
from app.services.base_service import BaseService
from app.services.comparison_service import ComparisonService
from app.services.memorix_description_parser import MemorixDescriptionParser
from app.services.memorix_service import MemorixService
from app.services.person_service import PersonService


class PhotoService(BaseService[PhotoRepository]):
    """Bedrijfslogica rondom foto's."""

    def __init__(
        self,
        repository: PhotoRepository | None = None,
        *,
        person_repository: PersonRepository | None = None,
        comment_repository: CommentRepository | None = None,
        history_repository: HistoryRepository | None = None,
        memorix_service: MemorixService | None = None,
        comparison_service: ComparisonService | None = None,
        description_parser: MemorixDescriptionParser | None = None,
    ) -> None:
        """Initialiseer de service en zijn repositoryafhankelijkheden."""

        super().__init__(repository or PhotoRepository())

        self.person_repository = person_repository or PersonRepository()
        self.comment_repository = comment_repository or CommentRepository()
        self.history_repository = history_repository or HistoryRepository()
        self.memorix_service = memorix_service or MemorixService()
        self.comparison_service = comparison_service or ComparisonService()
        self.description_parser = description_parser or MemorixDescriptionParser()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def get(
        self,
        photo_id: int,
    ) -> Photo | None:
        """Haal een foto op via de primaire sleutel."""

        return self.repository.get(photo_id)

    def get_required(
        self,
        photo_id: int,
    ) -> Photo:
        """Haal een foto op of meld dat deze niet bestaat."""

        photo = self.repository.get(photo_id)

        if photo is None:
            raise NotFoundError(
                "De foto bestaat niet.",
                code="PHOTO_NOT_FOUND",
                details={
                    "photo_id": photo_id,
                },
            )

        return photo

    def get_all(self) -> list[Photo]:
        """Geef alle foto's terug."""

        return self.repository.get_all()

    def get_landing_page(
        self,
        *,
        search: str = "",
        status: str | None = None,
        location: str = "",
        sort: str = "photo_number",
        direction: str = "asc",
        visible_only: bool = False,
        include_comparison: bool = False,
    ) -> dict[str, Any]:
        """Geef gefilterde live foto-informatie voor de landingspagina."""

        items = [
            self._build_landing_item(
                photo,
                include_comparison=include_comparison,
            )
            for photo in self.repository.get_for_landing(
                None, visible_only=visible_only
            )
        ]
        locations = sorted(
            {item["location"] for item in items if item["location"]},
            key=str.casefold,
        )

        normalized_search = search.casefold()
        normalized_location = location.casefold()

        if normalized_search:
            items = [
                item
                for item in items
                if normalized_search
                in " ".join((
                    item["photo_number"],
                    item["subject"],
                    item["date"],
                    item["location"],
                    item.get("description", ""),
                    item.get("person_names", ""),
                    item.get("mm_search_text", ""),
                )).casefold()
            ]

        if normalized_location:
            items = [
                item
                for item in items
                if item["location"].casefold() == normalized_location
            ]

        if status:
            items = [item for item in items if item["progress_status"] == status]

        sort_key = {
            "photo_number": lambda item: item["photo_number"].casefold(),
            "subject": lambda item: item["subject"].casefold(),
            "date": lambda item: item["date"].casefold(),
            "location": lambda item: item["location"].casefold(),
            "status": lambda item: item["progress_status"],
        }[sort]
        items.sort(key=sort_key, reverse=direction == "desc")

        return {
            "items": items,
            "locations": locations,
        }

    def get_detail(
        self,
        photo_id: int,
    ) -> dict[str, Any]:
        """Geef één foto met de live MM-afbeeldingsbron terug."""

        return self.get_accessible_detail(photo_id, include_hidden=True)

    def get_accessible_detail(
        self,
        photo_id: int,
        *,
        include_hidden: bool,
        include_comparison: bool = True,
    ) -> dict[str, Any]:
        """Geef fotodetails terug wanneer de gebruiker de foto mag bekijken."""

        photo = self.get_required(photo_id)
        if not include_hidden and not photo.is_visible:
            raise NotFoundError(
                "De foto bestaat niet.",
                code="PHOTO_NOT_FOUND",
                details={"photo_id": photo_id},
            )

        source_data = self.memorix_service.get_photo_data(photo.mm_id)
        previous_photo = self.repository.get_previous(photo.photo_number)
        next_photo = self.repository.get_next(photo.photo_number)

        parsed_description = self.description_parser.parse(
            str(source_data.get("description_raw", source_data.get("description", "")))
        )
        comparison_source = dict(source_data)
        comparison_source["description"] = parsed_description.description
        persons = self.person_repository.get_by_photo(photo.id)
        comparison = (
            self.comparison_service.compare_photo(
                mm_data=comparison_source,
                fno_data=self._local_metadata(photo),
                mm_names=parsed_description.names,
                fno_persons=persons,
                names_reliable=parsed_description.reliable,
                reason=parsed_description.reason,
            )
            if include_comparison
            else None
        )

        effective_metadata = self._effective_metadata(photo)
        detail = {
            "id": photo.id,
            "mm_id": photo.mm_id,
            "photo_number": photo.photo_number,
            "publication_status": photo.publication_status,
            "progress_status": self._get_progress_status(
                photo,
                metadata=effective_metadata,
            ),
            "is_visible": photo.is_visible,
            "is_complete": photo.is_complete,
            "person_display_mode": photo.person_display_mode,
            "label_size": photo.label_size,
            "person_display_count": photo.person_display_count,
            "previous_photo_id": previous_photo.id if previous_photo else None,
            "next_photo_id": next_photo.id if next_photo else None,
            "image_source": source_data["image_source"],
            **effective_metadata,
        }
        if comparison is not None:
            detail["comparison"] = comparison
        return detail

    def get_by_mm_id(
        self,
        mm_id: str,
    ) -> Photo | None:
        """Zoek een foto op MM-ID."""

        return self.repository.get_by_mm_id(mm_id)

    def get_by_photo_number(
        self,
        photo_number: str,
    ) -> Photo | None:
        """Zoek een foto op fotonummer."""

        return self.repository.get_by_photo_number(photo_number)

    def get_previous_photo(
        self,
        photo_id: int,
    ) -> Photo | None:
        """Geef de vorige foto op basis van een foto-ID."""

        photo = self.repository.get(photo_id)

        if photo is None:
            return None

        return self.repository.get_previous(photo.photo_number)

    def get_next_photo(
        self,
        photo_id: int,
    ) -> Photo | None:
        """Geef de volgende foto op basis van een foto-ID."""

        photo = self.repository.get(photo_id)

        if photo is None:
            return None

        return self.repository.get_next(photo.photo_number)

    def set_publication_status(
        self,
        photo_id: int,
        publication_status: PublicationStatus,
        *,
        user_id: int | None = None,
    ) -> Photo:
        """Wijzig de publicatiestatus via één centrale ingang."""

        handlers = {
            PublicationStatus.CONCEPT: self.set_concept,
            PublicationStatus.PUBLISHED: self.publish,
            PublicationStatus.HIDDEN: self.hide,
        }

        return handlers[publication_status](photo_id, user_id=user_id)

    def publish(
        self,
        photo_id: int,
        *,
        user_id: int | None = None,
    ) -> Photo:
        """Publiceer een foto en registreer de wijziging."""

        return self._change_publication_status(
            photo_id=photo_id,
            new_status=PublicationStatus.PUBLISHED,
            event_type=HistoryEventType.PHOTO_PUBLISHED,
            description="Foto gepubliceerd",
            user_id=user_id,
        )

    def hide(
        self,
        photo_id: int,
        *,
        user_id: int | None = None,
    ) -> Photo:
        """Verberg een foto en registreer de wijziging."""

        return self._change_publication_status(
            photo_id=photo_id,
            new_status=PublicationStatus.HIDDEN,
            event_type=HistoryEventType.PHOTO_HIDDEN,
            description="Foto verborgen",
            user_id=user_id,
        )

    def set_concept(
        self,
        photo_id: int,
        *,
        user_id: int | None = None,
    ) -> Photo:
        """Zet een foto terug naar conceptstatus."""

        return self._change_publication_status(
            photo_id=photo_id,
            new_status=PublicationStatus.CONCEPT,
            event_type=HistoryEventType.PHOTO_CONCEPT,
            description="Foto als concept ingesteld",
            user_id=user_id,
        )

    def import_from_memorix(
        self,
        *,
        mm_id: str,
        photo_number: str,
        user_id: int | None = None,
    ) -> Photo:
        """Voeg één MM-record als lokale conceptfoto toe."""

        normalized_mm_id = mm_id.strip()
        normalized_photo_number = photo_number.strip()

        if not normalized_mm_id:
            raise ValidationError(
                "Maior Memorix-ID is verplicht.",
                code="MM_ID_REQUIRED",
            )

        if not normalized_photo_number:
            raise ValidationError(
                "Fotonummer is verplicht.",
                code="PHOTO_NUMBER_REQUIRED",
            )

        if self.repository.get_by_mm_id(normalized_mm_id) is not None:
            raise ConflictError(
                "Deze Maior Memorix-foto is al aan FNO toegevoegd.",
                code="PHOTO_ALREADY_EXISTS",
                details={"mm_id": normalized_mm_id},
            )

        if self.repository.get_by_photo_number(normalized_photo_number) is not None:
            raise ConflictError(
                "Dit fotonummer bestaat al binnen FNO.",
                code="PHOTO_NUMBER_ALREADY_EXISTS",
                details={"photo_number": normalized_photo_number},
            )

        self.memorix_service.get_photo_data(normalized_mm_id)

        photo = self.repository.add(
            Photo(
                mm_id=normalized_mm_id,
                photo_number=normalized_photo_number,
                publication_status=PublicationStatus.CONCEPT,
            )
        )
        self.repository.flush()
        self.history_repository.create(
            photo_id=photo.id,
            user_id=user_id,
            event_type=HistoryEventType.PHOTO_IMPORTED,
            description="Foto uit Maior Memorix toegevoegd",
            new_value=normalized_mm_id,
        )
        self._commit()

        return photo

    def update_local_metadata(
        self,
        photo_id: int,
        *,
        subject: str,
        date: str,
        location: str,
        description: str,
        user_id: int | None = None,
    ) -> Photo:
        """Wijzig de lokale FNO-metadata van een foto."""

        photo = self.get_required(photo_id)
        old_value = " | ".join(
            value or ""
            for value in (
                photo.local_subject,
                photo.local_date,
                photo.local_location,
                photo.local_description,
            )
        )
        photo.local_subject = subject.strip() or None
        photo.local_date = date.strip() or None
        photo.local_location = location.strip() or None
        photo.local_description = description.strip() or None
        self.history_repository.create(
            photo_id=photo.id,
            user_id=user_id,
            event_type=HistoryEventType.METADATA_CHANGED,
            description="Lokale fotometadata gewijzigd",
            old_value=old_value,
            new_value=" | ".join((subject, date, location, description)),
        )
        self._commit()
        return photo

    def update_management(
        self,
        photo_id: int,
        *,
        is_visible: bool,
        is_complete: bool,
        user_id: int | None = None,
    ) -> Photo:
        """Wijzig zichtbaarheid en gereedmelding van een foto."""

        photo = self.get_required(photo_id)
        old_visible = photo.is_visible
        old_complete = photo.is_complete
        photo.is_visible = is_visible
        photo.is_complete = is_complete
        if old_visible != is_visible:
            self.history_repository.create(
                photo_id=photo.id,
                user_id=user_id,
                event_type=HistoryEventType.PHOTO_VISIBILITY_CHANGED,
                description="Zichtbaarheid foto gewijzigd",
                old_value=str(old_visible),
                new_value=str(is_visible),
            )
        if old_complete != is_complete:
            self.history_repository.create(
                photo_id=photo.id,
                user_id=user_id,
                event_type=HistoryEventType.PHOTO_COMPLETION_CHANGED,
                description="Gereedmelding foto gewijzigd",
                old_value=str(old_complete),
                new_value=str(is_complete),
            )
        self._commit()
        return photo

    def update_person_display_mode(
        self,
        photo_id: int,
        *,
        person_display_mode: str,
        person_display_count: int = 1,
        user_id: int | None = None,
    ) -> Photo:
        """Wijzig de presentatie en het aantal personenregels van een foto."""

        if person_display_mode not in {"numbered", "left_to_right", "single_person"}:
            raise ValidationError(
                "Ongeldige personenweergave.",
                code="INVALID_PERSON_DISPLAY_MODE",
            )

        if person_display_mode == "left_to_right":
            if person_display_count < 2 or person_display_count > 30:
                raise ValidationError(
                    "v.l.n.r. ondersteunt 2 tot en met 30 personen.",
                    code="INVALID_PERSON_DISPLAY_COUNT",
                )
            target_count = person_display_count
        elif person_display_mode == "single_person":
            target_count = 1
        else:
            target_count = max(1, person_display_count)

        photo = self.get_required(photo_id)
        old_mode = photo.person_display_mode
        old_count = photo.person_display_count

        if person_display_mode != "numbered":
            PersonService().set_display_person_count(
                photo_id=photo_id,
                count=target_count,
                user_id=user_id,
            )

        photo.person_display_mode = person_display_mode
        photo.person_display_count = target_count
        if old_mode != person_display_mode or old_count != target_count:
            self.history_repository.create(
                photo_id=photo.id,
                user_id=user_id,
                event_type=HistoryEventType.PHOTO_PERSON_DISPLAY_MODE_CHANGED,
                description="Personenweergave gewijzigd",
                old_value=f"{old_mode}:{old_count}",
                new_value=f"{person_display_mode}:{target_count}",
            )
            self._commit()
        return photo

    def update_label_size(
        self,
        photo_id: int,
        *,
        label_size: int,
        user_id: int | None = None,
    ) -> Photo:
        """Wijzig de labelgrootte van een foto."""

        if label_size < 5 or label_size > 30:
            raise ValidationError(
                "Labelgrootte moet tussen 5 en 30 liggen.",
                code="INVALID_LABEL_SIZE",
            )

        photo = self.get_required(photo_id)
        old_size = photo.label_size
        if old_size == label_size:
            return photo

        photo.label_size = label_size
        self.history_repository.create(
            photo_id=photo.id,
            user_id=user_id,
            event_type=HistoryEventType.PHOTO_LABEL_SIZE_CHANGED,
            description="Labelgrootte gewijzigd",
            old_value=str(old_size),
            new_value=str(label_size),
        )
        self._commit()
        return photo

    def delete_from_fno(self, photo_id: int) -> None:
        """Verwijder een foto en alle FNO-gegevens zonder Maior Memorix te wijzigen."""

        photo = self.get_required(photo_id)
        self.repository.delete(photo)
        self._commit()

    def count_labels(
        self,
        photo_id: int,
    ) -> int:
        """Geef het aantal labels op een foto terug."""

        self.get_required(photo_id)

        return len(self.person_repository.get_by_photo(photo_id))

    def count_open_comments(
        self,
        photo_id: int,
    ) -> int:
        """Geef het aantal open opmerkingen bij een foto terug."""

        self.get_required(photo_id)

        return self.comment_repository.count_open_by_photo(photo_id)

    def has_labels(
        self,
        photo_id: int,
    ) -> bool:
        """Controleer of een foto minimaal één label heeft."""

        return self.count_labels(photo_id) > 0

    def get_summary(
        self,
        photo_id: int,
    ) -> dict[str, Any]:
        """Geef een compact functioneel foto-overzicht terug."""

        photo = self.get_required(photo_id)

        label_count = len(self.person_repository.get_by_photo(photo_id))

        open_comment_count = self.comment_repository.count_open_by_photo(photo_id)

        return {
            "id": photo.id,
            "mm_id": photo.mm_id,
            "photo_number": photo.photo_number,
            "publication_status": PublicationStatus(
                photo.publication_status
            ).name.lower(),
            "label_count": label_count,
            "has_labels": label_count > 0,
            "open_comment_count": open_comment_count,
        }

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------

    def _build_landing_item(
        self,
        photo: Photo,
        *,
        include_comparison: bool,
    ) -> dict[str, Any]:
        """Combineer lokale fotogegevens met live MM-lijstgegevens."""

        try:
            source_data = self.memorix_service.get_landing_data(photo.mm_id)
        except FNOError:
            fields = photo.mm_metadata if isinstance(photo.mm_metadata, dict) else {}
            source_data = self.memorix_service.get_landing_data_from_fields(fields)

        parsed_description = self.description_parser.parse(
            str(source_data.get("description_raw", source_data.get("description", "")))
        )
        comparison_source = dict(source_data)
        comparison_source["description"] = parsed_description.description
        persons = self.person_repository.get_by_photo(photo.id)
        comparison = (
            self.comparison_service.compare_photo(
                mm_data=comparison_source,
                fno_data=self._local_metadata(photo),
                mm_names=parsed_description.names,
                fno_persons=persons,
                names_reliable=parsed_description.reliable,
                reason=parsed_description.reason,
            )
            if include_comparison
            else None
        )
        effective_metadata = self._effective_metadata(photo)
        item = {
            "id": photo.id,
            "mm_id": photo.mm_id,
            "photo_number": photo.photo_number,
            "publication_status": PublicationStatus(photo.publication_status),
            "progress_status": self._get_progress_status(
                photo,
                metadata=effective_metadata,
            ),
            "is_visible": photo.is_visible,
            "is_complete": photo.is_complete,
            "thumbnail_url": source_data.get("thumbnail_url", ""),
            **effective_metadata,
            "person_names": " ".join(
                person.current_name or "" for person in photo.persons
            ),
            "mm_search_text": " ".join(
                str(value)
                for values in (photo.mm_metadata or {}).values()
                for value in (values if isinstance(values, list) else [values])
            ),
        }
        if comparison is not None:
            item["comparison"] = comparison
        return item

    @staticmethod
    def _effective_metadata(photo: Photo) -> dict[str, str]:
        """Geef uitsluitend daadwerkelijk opgeslagen FNO-metadata terug."""

        return {
            "subject": photo.local_subject or "",
            "date": photo.local_date or "",
            "location": photo.local_location or "",
            "description": photo.local_description or "",
        }

    @staticmethod
    def _local_metadata(photo: Photo) -> dict[str, str | None]:
        """Geef de lokaal beheerde metadata van een foto."""

        return {
            "subject": photo.local_subject,
            "date": photo.local_date,
            "location": photo.local_location,
            "description": photo.local_description,
        }

    def get_progress_status(self, photo: Photo) -> str:
        """Bepaal de voortgang op basis van lokaal opgeslagen FNO-data."""

        return self._get_progress_status(photo)

    @staticmethod
    def _get_progress_status(
        photo: Photo,
        *,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Bepaal voortgang met optioneel read-only zichtbare metadata."""

        if photo.is_complete:
            return "complete"
        if metadata is None:
            has_metadata = any((
                photo.local_subject,
                photo.local_date,
                photo.local_location,
                photo.local_description,
            ))
        else:
            has_metadata = any(metadata.values())
        has_names = any(person.current_name for person in photo.persons)
        return "partial" if has_metadata or has_names else "empty"

    def _change_publication_status(
        self,
        *,
        photo_id: int,
        new_status: PublicationStatus,
        event_type: HistoryEventType,
        description: str,
        user_id: int | None,
    ) -> Photo:
        """Wijzig de publicatiestatus en registreer de gebeurtenis."""

        photo = self.get_required(photo_id)

        old_status = PublicationStatus(photo.publication_status)

        if old_status == new_status:
            return photo

        photo.publication_status = new_status

        self.history_repository.create(
            photo_id=photo.id,
            user_id=user_id,
            event_type=event_type,
            description=description,
            old_value=old_status.name.lower(),
            new_value=new_status.name.lower(),
        )

        self._commit()

        return photo
