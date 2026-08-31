"""Repository voor gelabelde personen op foto's."""

from __future__ import annotations

from sqlalchemy import func, select

from app.extensions import db
from app.models import Person
from app.repositories.base_repository import BaseRepository


class PersonRepository(BaseRepository[Person]):
    """Databasebewerkingen voor de Person-entiteit."""

    model = Person

    def get_by_photo(self, photo_id: int) -> list[Person]:
        """Geef alle personen van een foto op labelvolgorde terug."""

        statement = (
            select(Person)
            .where(Person.photo_id == photo_id)
            .order_by(Person.label_number)
        )

        return list(db.session.scalars(statement))

    def get_next_label_number(self, photo_id: int) -> int:
        """Geef het eerstvolgende labelnummer voor een foto."""

        statement = select(func.max(Person.label_number)).where(
            Person.photo_id == photo_id
        )
        maximum = db.session.scalar(statement)

        return (maximum or 0) + 1

    def find_by_number(
        self,
        photo_id: int,
        label_number: int,
    ) -> Person | None:
        """Zoek een persoon via foto-ID en labelnummer."""

        statement = select(Person).where(
            Person.photo_id == photo_id,
            Person.label_number == label_number,
        )

        return db.session.scalar(statement)

    def find_by_name(self, name: str) -> list[Person]:
        """Zoek personen op een gedeeltelijke, hoofdletterongevoelige naam."""

        normalized_name = name.strip().lower()

        if not normalized_name:
            return []

        statement = (
            select(Person)
            .where(func.lower(Person.current_name).contains(normalized_name))
            .order_by(
                Person.current_name,
                Person.photo_id,
                Person.label_number,
            )
        )

        return list(db.session.scalars(statement))

    def exists_label_number(
        self,
        photo_id: int,
        label_number: int,
        *,
        exclude_person_id: int | None = None,
    ) -> bool:
        """Controleer of een labelnummer binnen een foto bestaat."""

        statement = select(Person.id).where(
            Person.photo_id == photo_id,
            Person.label_number == label_number,
        )

        if exclude_person_id is not None:
            statement = statement.where(Person.id != exclude_person_id)

        return db.session.scalar(statement.limit(1)) is not None

    def create(
        self,
        *,
        photo_id: int,
        label_number: int,
        x_position: float,
        y_position: float,
        current_name: str | None = None,
    ) -> Person:
        """Maak een gelabelde persoon aan."""

        person = Person(
            photo_id=photo_id,
            label_number=label_number,
            x_position=x_position,
            y_position=y_position,
            current_name=current_name,
        )

        return self.add(person)

    def update(
        self,
        person: Person,
        *,
        current_name: str | None = None,
    ) -> Person:
        """Wijzig de actuele naam van een persoon."""

        person.current_name = current_name

        return person

    def move(
        self,
        person: Person,
        *,
        x_position: float,
        y_position: float,
    ) -> Person:
        """Wijzig de relatieve labelpositie."""

        person.x_position = x_position
        person.y_position = y_position

        return person

    def renumber(
        self,
        person: Person,
        *,
        label_number: int,
    ) -> Person:
        """Wijzig uitsluitend het zichtbare labelnummer."""

        person.label_number = label_number

        return person
