"""SQLAlchemy-model voor MM-importopdrachten."""

from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.mixins import TimestampMixin


class MmImportJob(TimestampMixin, BaseModel):
    """Auditregistratie van één MM-bulkimport."""

    __tablename__ = "mm_import_job"

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    filters: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    found_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
