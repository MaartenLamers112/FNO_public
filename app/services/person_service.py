"""Bedrijfslogica voor personen en fotolabels."""

from __future__ import annotations

from app.enums.history_event_type import HistoryEventType
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Person, Photo
from app.repositories import (
    HistoryRepository,
    PersonRepository,
    PhotoRepository,
)
from app.services.base_service import BaseService

TEMP_LABEL_OFFSET = 1_000_000


class PersonService(BaseService[PersonRepository]):
    """Bedrijfslogica rondom personen en labels."""

    def __init__(
        self,
        repository: PersonRepository | None = None,
        *,
        photo_repository: PhotoRepository | None = None,
        history_repository: HistoryRepository | None = None,
    ) -> None:
        """Initialiseer de service en zijn repositoryafhankelijkheden."""

        super().__init__(repository or PersonRepository())

        self.photo_repository = photo_repository or PhotoRepository()
        self.history_repository = history_repository or HistoryRepository()

    def get(
        self,
        person_id: int,
    ) -> Person | None:
        """Haal een persoon op via de primaire sleutel."""

        return self.repository.get(person_id)

    def get_by_photo(
        self,
        photo_id: int,
    ) -> list[Person]:
        """Geef alle persoonslabels van een bestaande foto terug."""

        self._get_required_photo(photo_id)

        return self.repository.get_by_photo(photo_id)

    def create_next_label(
        self,
        *,
        photo_id: int,
        x_position: float,
        y_position: float,
        user_id: int | None = None,
    ) -> Person:
        """Maak een label aan met het eerstvolgende nummer."""

        self._get_required_photo(photo_id)

        label_number = self.repository.get_next_label_number(photo_id)

        return self.create_label(
            photo_id=photo_id,
            label_number=label_number,
            x_position=x_position,
            y_position=y_position,
            user_id=user_id,
        )

    def create_label(
        self,
        *,
        photo_id: int,
        label_number: int,
        x_position: float,
        y_position: float,
        current_name: str | None = None,
        user_id: int | None = None,
    ) -> Person:
        """Maak een nieuw persoonslabel aan."""

        self._get_required_photo(photo_id)
        self._validate_label_number(label_number)
        self._validate_position(x_position, y_position)

        if self.repository.exists_label_number(
            photo_id,
            label_number,
        ):
            raise ConflictError(
                f"Labelnummer {label_number} bestaat al op deze foto.",
                code="LABEL_NUMBER_ALREADY_EXISTS",
                details={
                    "photo_id": photo_id,
                    "label_number": label_number,
                },
            )

        normalized_name = self._normalize_name(current_name)

        person = self.repository.create(
            photo_id=photo_id,
            label_number=label_number,
            x_position=x_position,
            y_position=y_position,
            current_name=normalized_name,
        )

        self.repository.flush()

        self._create_history(
            photo_id=photo_id,
            person_id=person.id,
            event_type=HistoryEventType.LABEL_CREATED,
            description=f"Label {label_number} toegevoegd",
            user_id=user_id,
        )

        self._commit()

        return person

    def move_label(
        self,
        *,
        person_id: int,
        x_position: float,
        y_position: float,
        user_id: int | None = None,
    ) -> Person:
        """Verplaats een label."""

        person = self._get_required_person(person_id)

        self._validate_position(
            x_position,
            y_position,
        )

        old_position = f"{person.x_position:.4f},{person.y_position:.4f}"

        person.x_position = x_position
        person.y_position = y_position

        new_position = f"{x_position:.4f},{y_position:.4f}"

        self._create_history(
            photo_id=person.photo_id,
            person_id=person.id,
            event_type=HistoryEventType.LABEL_MOVED,
            description=f"Label {person.label_number} verplaatst",
            user_id=user_id,
            old_value=old_position,
            new_value=new_position,
        )

        self._commit()

        return person

    def renumber_label(
        self,
        *,
        person_id: int,
        new_label_number: int,
        user_id: int | None = None,
    ) -> Person:
        """Wijzig het labelnummer van een persoon."""

        person = self._get_required_person(person_id)
        old_label_number = person.label_number

        self._validate_new_label_number(
            photo_id=person.photo_id,
            new_label_number=new_label_number,
        )

        if old_label_number == new_label_number:
            return person

        persons = self.repository.get_by_photo(person.photo_id)

        persons.remove(person)
        persons.insert(new_label_number - 1, person)

        self._resequence_labels(persons)

        self._create_history(
            photo_id=person.photo_id,
            person_id=person.id,
            event_type=HistoryEventType.LABEL_RENUMBERED,
            description=(f"Label {old_label_number} gewijzigd naar {new_label_number}"),
            user_id=user_id,
            old_value=str(old_label_number),
            new_value=str(new_label_number),
        )

        self._commit()

        return person

    def renumber_by_position(
        self,
        *,
        photo_id: int,
        user_id: int | None = None,
    ) -> list[Person]:
        """Hernummer labels per rij van boven naar beneden en links naar rechts."""

        self._get_required_photo(photo_id)
        persons = self.repository.get_by_photo(photo_id)
        if len(persons) < 2:
            return persons

        ordered = self._sort_by_reading_order(persons)
        old_order = ",".join(str(person.id) for person in persons)
        new_order = ",".join(str(person.id) for person in ordered)
        if old_order == new_order and all(
            person.label_number == index
            for index, person in enumerate(ordered, start=1)
        ):
            return ordered

        self._resequence_labels(ordered)
        self._create_history(
            photo_id=photo_id,
            person_id=None,
            event_type=HistoryEventType.LABEL_RENUMBERED,
            description="Alle labels automatisch hernummerd",
            user_id=user_id,
            old_value=old_order,
            new_value=new_order,
        )
        self._commit()
        return ordered

    @staticmethod
    def _sort_by_reading_order(persons: list[Person]) -> list[Person]:
        """Sorteer labels robuust in visuele rijen."""

        row_tolerance = 0.06
        rows: list[list[Person]] = []
        ordered_persons = sorted(
            persons,
            key=lambda item: (item.y_position, item.x_position),
        )
        for person in ordered_persons:
            if not rows:
                rows.append([person])
                continue
            row_average = sum(item.y_position for item in rows[-1]) / len(rows[-1])
            if abs(person.y_position - row_average) <= row_tolerance:
                rows[-1].append(person)
            else:
                rows.append([person])

        return [
            person
            for row in rows
            for person in sorted(row, key=lambda item: item.x_position)
        ]

    def rename_person(
        self,
        *,
        person_id: int,
        new_name: str | None,
        user_id: int | None = None,
        can_override_lock: bool = False,
    ) -> Person:
        """Wijzig de naam van een persoon."""

        person = self._get_required_person(person_id)
        if person.name_locked and not can_override_lock:
            raise ValidationError(
                "Deze naam is vergrendeld.",
                code="PERSON_NAME_LOCKED",
                details={"person_id": person_id},
            )

        old_name = person.current_name
        normalized_name = self._normalize_name(new_name)

        if old_name == normalized_name:
            return person

        person.current_name = normalized_name

        if old_name is None and normalized_name is not None:
            event_type = HistoryEventType.NAME_CREATED
            description = f"Naam toegevoegd aan label {person.label_number}"
        elif old_name is not None and normalized_name is None:
            event_type = HistoryEventType.NAME_CLEARED
            description = f"Naam verwijderd van label {person.label_number}"
        else:
            event_type = HistoryEventType.NAME_CHANGED
            description = f"Naam gewijzigd bij label {person.label_number}"

        self._create_history(
            photo_id=person.photo_id,
            person_id=person.id,
            event_type=event_type,
            description=description,
            user_id=user_id,
            old_value=old_name,
            new_value=normalized_name,
        )

        self._commit()

        return person

    def set_name_lock(
        self,
        *,
        person_id: int,
        name_locked: bool,
        user_id: int | None = None,
    ) -> Person:
        """Vergrendel of ontgrendel een persoonsnaam."""

        person = self._get_required_person(person_id)
        if person.name_locked == name_locked:
            return person
        person.name_locked = name_locked
        self._create_history(
            photo_id=person.photo_id,
            person_id=person.id,
            event_type=(
                HistoryEventType.NAME_LOCKED
                if name_locked
                else HistoryEventType.NAME_UNLOCKED
            ),
            description=("Naam vergrendeld" if name_locked else "Naam ontgrendeld"),
            user_id=user_id,
            old_value=str(not name_locked),
            new_value=str(name_locked),
        )
        self._commit()
        return person

    def create_labels_from_detections(
        self,
        *,
        photo_id: int,
        positions: list[tuple[float, float]],
        user_id: int | None = None,
    ) -> list[Person]:
        """Sla nieuwe automatisch gedetecteerde labels in één transactie op."""

        self._get_required_photo(photo_id)
        if not positions:
            raise ValidationError(
                "Er zijn geen nieuwe detectieposities ontvangen.",
                code="DETECTION_PROPOSALS_REQUIRED",
            )
        if len(positions) > 250:
            raise ValidationError(
                "Er kunnen maximaal 250 labels tegelijk worden toegevoegd.",
                code="DETECTION_PROPOSALS_TOO_MANY",
            )

        for x_position, y_position in positions:
            self._validate_position(x_position, y_position)

        next_label_number = self.repository.get_next_label_number(photo_id)
        persons: list[Person] = []
        for offset, (x_position, y_position) in enumerate(positions):
            label_number = next_label_number + offset
            person = self.repository.create(
                photo_id=photo_id,
                label_number=label_number,
                x_position=x_position,
                y_position=y_position,
                current_name=None,
            )
            persons.append(person)

        self.repository.flush()
        for person in persons:
            self._create_history(
                photo_id=photo_id,
                person_id=person.id,
                event_type=HistoryEventType.LABEL_CREATED,
                description=f"Label {person.label_number} automatisch toegevoegd",
                user_id=user_id,
            )

        self._commit()
        return persons

    def set_display_person_count(
        self,
        *,
        photo_id: int,
        count: int,
        user_id: int | None = None,
    ) -> list[Person]:
        """Pas het aantal naamregels voor een ongenummerde weergave aan."""

        self._get_required_photo(photo_id)
        if count < 1 or count > 30:
            raise ValidationError(
                "Aantal personen moet tussen 1 en 30 liggen.",
                code="INVALID_PERSON_DISPLAY_COUNT",
            )

        persons = self.repository.get_by_photo(photo_id)
        ordered = sorted(
            persons,
            key=lambda person: (
                person.x_position,
                person.y_position,
                person.label_number,
            ),
        )

        if len(ordered) == count:
            return ordered

        if len(ordered) > count:
            for person in ordered[count:]:
                self.repository.delete(person)
            ordered = ordered[:count]
            self.repository.flush()

        if len(ordered) < count:
            next_label = self.repository.get_next_label_number(photo_id)
            missing = count - len(ordered)
            start_x = max((person.x_position for person in ordered), default=0.0)
            step = (1.0 - start_x) / (missing + 1)
            for offset in range(missing):
                person = self.repository.create(
                    photo_id=photo_id,
                    label_number=next_label + offset,
                    x_position=start_x + step * (offset + 1),
                    y_position=0.5,
                    current_name=None,
                )
                ordered.append(person)
            self.repository.flush()

        self._resequence_labels(ordered)
        self._create_history(
            photo_id=photo_id,
            person_id=None,
            event_type=HistoryEventType.LABEL_RENUMBERED,
            description=f"Aantal personenregels ingesteld op {count}",
            user_id=user_id,
            new_value=str(count),
        )
        self._commit()
        return ordered

    def delete_label(
        self,
        *,
        person_id: int,
        user_id: int | None = None,
    ) -> None:
        """Verwijder een label en nummer de resterende labels opnieuw."""

        person = self._get_required_person(person_id)

        photo_id = person.photo_id
        old_label_number = person.label_number
        old_name = person.current_name

        remaining_persons = [
            current_person
            for current_person in self.repository.get_by_photo(photo_id)
            if current_person.id != person.id
        ]

        self.repository.delete(person)
        self.repository.flush()

        if remaining_persons:
            self._resequence_labels(remaining_persons)

        description = f"Label {old_label_number} verwijderd"

        if old_name is not None:
            description += f" ({old_name})"

        self._create_history(
            photo_id=photo_id,
            person_id=None,
            event_type=HistoryEventType.LABEL_DELETED,
            description=description,
            user_id=user_id,
            old_value=str(old_label_number),
            new_value=None,
        )

        self._commit()

    def delete_all_labels(
        self,
        *,
        photo_id: int,
        user_id: int | None = None,
    ) -> int:
        """Verwijder alle labels van een foto en registreer één auditregel."""

        self._get_required_photo(photo_id)
        persons = self.repository.get_by_photo(photo_id)
        count = len(persons)

        for person in persons:
            self.repository.delete(person)

        if count:
            self.repository.flush()
            self._create_history(
                photo_id=photo_id,
                person_id=None,
                event_type=HistoryEventType.LABEL_DELETED,
                description=f"Alle {count} labels verwijderd",
                user_id=user_id,
                old_value=str(count),
                new_value=None,
            )
            self._commit()

        return count

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

        person = self.repository.get(person_id)

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
    def _validate_label_number(label_number: int) -> None:
        """Controleer of het labelnummer geldig is."""

        if label_number < 1:
            raise ValidationError(
                "Het labelnummer moet minimaal 1 zijn.",
                code="LABEL_NUMBER_INVALID",
                details={
                    "label_number": label_number,
                },
            )

    def _validate_new_label_number(
        self,
        *,
        photo_id: int,
        new_label_number: int,
    ) -> None:
        """Controleer of een nieuw labelnummer geldig is."""

        persons = self.repository.get_by_photo(photo_id)

        if not 1 <= new_label_number <= len(persons):
            raise ValidationError(
                "Het nieuwe labelnummer valt buiten het geldige bereik.",
                code="LABEL_NUMBER_OUT_OF_RANGE",
                details={
                    "photo_id": photo_id,
                    "new_label_number": new_label_number,
                    "maximum": len(persons),
                },
            )

    @staticmethod
    def _validate_position(
        x_position: float,
        y_position: float,
    ) -> None:
        """Controleer relatieve labelcoördinaten."""

        if not 0.0 <= x_position <= 1.0:
            raise ValidationError(
                "De horizontale positie moet tussen 0 en 1 liggen.",
                code="LABEL_X_POSITION_INVALID",
                details={
                    "x_position": x_position,
                },
            )

        if not 0.0 <= y_position <= 1.0:
            raise ValidationError(
                "De verticale positie moet tussen 0 en 1 liggen.",
                code="LABEL_Y_POSITION_INVALID",
                details={
                    "y_position": y_position,
                },
            )

    @staticmethod
    def _normalize_name(
        current_name: str | None,
    ) -> str | None:
        """Verwijder overbodige witruimte uit een optionele naam."""

        if current_name is None:
            return None

        normalized_name = current_name.strip()

        return normalized_name or None

    def _resequence_labels(
        self,
        persons: list[Person],
    ) -> None:
        """Geef alle labels opnieuw opeenvolgende nummers."""

        for person in persons:
            person.label_number += TEMP_LABEL_OFFSET

        self.repository.flush()

        for label_number, person in enumerate(
            persons,
            start=1,
        ):
            person.label_number = label_number

    def _create_history(
        self,
        *,
        photo_id: int,
        person_id: int | None,
        event_type: HistoryEventType,
        description: str,
        user_id: int | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> None:
        """Registreer een historie-item."""

        self.history_repository.create(
            photo_id=photo_id,
            person_id=person_id,
            user_id=user_id,
            event_type=event_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
        )
