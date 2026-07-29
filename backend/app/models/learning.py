import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_gap_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_gap_reports.id", ondelete="RESTRICT"), nullable=False
    )
    # enum-like: active / completed / archived
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roadmaps")
    skill_gap_report: Mapped["SkillGapReport"] = relationship("SkillGapReport", back_populates="roadmap")
    items: Mapped[list["RoadmapItem"]] = relationship("RoadmapItem", back_populates="roadmap", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_roadmaps_user_id", "user_id"),
    )


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(Text, nullable=False)
    # enum-like: course / article / project / milestone
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    # enum-like: beginner / intermediate / advanced
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)
    # enum-like: not_started / in_progress / completed
    status: Mapped[str] = mapped_column(Text, nullable=False, default="not_started", server_default="not_started")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="items")

    __table_args__ = (
        Index("ix_roadmap_items_roadmap_id", "roadmap_id"),
        Index("ix_roadmap_items_roadmap_id_sequence_order", "roadmap_id", "sequence_order"),
    )
