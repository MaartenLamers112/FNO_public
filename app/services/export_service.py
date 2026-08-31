"""Bedrijfslogica voor foto- en personenexports."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Any

from app.enums.publication_status import PublicationStatus
from app.repositories import CommentRepository, PersonRepository
from app.services.photo_service import PhotoService


@dataclass(frozen=True)
class PhotoExport:
    """Gegevens voor een technische foto-export."""

    photo: dict[str, Any]
    persons: list[dict[str, Any]]
    comments: list[dict[str, Any]]


class ExportService:
    """Maak exports van FNO-fotogegevens."""

    def __init__(
        self,
        *,
        photo_service: PhotoService | None = None,
        person_repository: PersonRepository | None = None,
        comment_repository: CommentRepository | None = None,
    ) -> None:
        """Initialiseer de exportafhankelijkheden."""

        self.photo_service = photo_service or PhotoService()
        self.person_repository = person_repository or PersonRepository()
        self.comment_repository = comment_repository or CommentRepository()

    def get_photo_export(self, photo_id: int) -> PhotoExport:
        """Geef actuele foto-, persoons- en opmerkingengegevens voor export."""

        detail = self.photo_service.get_detail(photo_id)
        persons = self.person_repository.get_by_photo(photo_id)
        if detail["person_display_mode"] == "left_to_right":
            persons = sorted(
                persons,
                key=lambda person: (person.x_position, person.y_position),
            )
        comments = self.comment_repository.get_by_photo(photo_id)

        return PhotoExport(
            photo={
                "id": detail["id"],
                "mm_id": detail["mm_id"],
                "photo_number": detail["photo_number"],
                "subject": detail["subject"],
                "date": detail["date"],
                "location": detail["location"],
                "description": detail["description"],
                "publication_status": PublicationStatus(
                    detail["publication_status"]
                ).name.lower(),
                "is_visible": detail["is_visible"],
                "is_complete": detail["is_complete"],
                "person_display_mode": detail["person_display_mode"],
            },
            persons=[
                {
                    "id": person.id,
                    "label_number": person.label_number,
                    "name": person.current_name or "",
                    "x_position": person.x_position,
                    "y_position": person.y_position,
                    "name_locked": person.name_locked,
                }
                for person in persons
            ],
            comments=[
                {
                    "id": comment.id,
                    "person_id": comment.person_id,
                    "content": comment.content,
                    "status": str(comment.status),
                }
                for comment in comments
            ],
        )

    def create_data_csv(self, photo_id: int) -> str:
        """Maak een CSV met alle voor MM bruikbare ingevulde gegevens."""

        export = self.get_photo_export(photo_id)
        photo = export.photo
        photo_comments = self._join_comments(export.comments, person_id=None)
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter=";")
        writer.writerow([
            "fotonummer",
            "onderwerp",
            "datering",
            "locatie",
            "beschrijving",
            "foto_opmerkingen",
            "labelnummer",
            "persoon",
            "persoon_opmerkingen",
        ])

        if not export.persons:
            writer.writerow([
                photo["photo_number"],
                photo["subject"],
                photo["date"],
                photo["location"],
                photo["description"],
                photo_comments,
                "",
                "",
                "",
            ])
            return output.getvalue()

        for person in export.persons:
            writer.writerow([
                photo["photo_number"],
                photo["subject"],
                photo["date"],
                photo["location"],
                photo["description"],
                photo_comments,
                (
                    person["label_number"]
                    if photo["person_display_mode"] == "numbered"
                    else (
                        "v.l.n.r."
                        if photo["person_display_mode"] == "left_to_right"
                        else "1 persoon"
                    )
                ),
                person["name"],
                self._join_comments(
                    export.comments,
                    person_id=person["id"],
                ),
            ])

        return output.getvalue()

    def create_text_export(self, photo_id: int) -> str:
        """Maak een leesbare tekstexport voor handmatige verwerking in MM."""

        export = self.get_photo_export(photo_id)
        photo = export.photo
        lines = [
            f"Fotonummer: {photo['photo_number']}",
            f"Onderwerp: {photo['subject']}",
            f"Datering: {photo['date']}",
            f"Locatie: {photo['location']}",
            "",
            "Beschrijving:",
            photo["description"],
            "",
            (
                "Personen (v.l.n.r.):"
                if photo["person_display_mode"] == "left_to_right"
                else (
                    "Persoon:"
                    if photo["person_display_mode"] == "single_person"
                    else "Personen:"
                )
            ),
        ]

        if export.persons:
            for person in export.persons:
                if photo["person_display_mode"] == "numbered":
                    lines.append(f"{person['label_number']}. {person['name']}")
                else:
                    lines.append(person["name"] or "Naam nog onbekend")
                person_comments = self._comments_for_person(
                    export.comments,
                    person_id=person["id"],
                )
                for comment in person_comments:
                    lines.append(f"   Opmerking: {comment['content']}")
        else:
            lines.append("Geen personen ingevuld.")

        photo_comments = self._comments_for_person(export.comments, person_id=None)
        lines.extend(["", "Foto-opmerkingen:"])
        if photo_comments:
            lines.extend(f"- {comment['content']}" for comment in photo_comments)
        else:
            lines.append("Geen foto-opmerkingen ingevuld.")

        return "\r\n".join(lines).rstrip() + "\r\n"

    @staticmethod
    def _comments_for_person(
        comments: list[dict[str, Any]],
        *,
        person_id: int | None,
    ) -> list[dict[str, Any]]:
        """Selecteer opmerkingen voor de foto of één persoon."""

        return [comment for comment in comments if comment["person_id"] == person_id]

    def _join_comments(
        self,
        comments: list[dict[str, Any]],
        *,
        person_id: int | None,
    ) -> str:
        """Voeg opmerkingen samen voor gebruik in één CSV-cel."""

        return "\n".join(
            comment["content"]
            for comment in self._comments_for_person(
                comments,
                person_id=person_id,
            )
        )
