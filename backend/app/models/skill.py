import uuid
from datetime import datetime
from sqlalchemy import Text, Float, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from pgvector.sqlalchemy import Vector


class SkillVector(Base):
    __tablename__ = "skill_vectors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    # vector(384) — MiniLM-style embedding dimension; adjust in embedding_service.py if model changes
    vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    raw_skills: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skill_vectors")
    resume: Mapped["Resume | None"] = relationship("Resume", back_populates="skill_vectors")
    skill_gap_reports: Mapped[list["SkillGapReport"]] = relationship("SkillGapReport", back_populates="skill_vector")

    __table_args__ = (
        Index("ix_skill_vectors_user_id", "user_id"),
        # ivfflat index created after seed data is loaded — see database.md §5
    )


class MarketSkillReference(Base):
    __tablename__ = "market_skill_reference"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    role_title: Mapped[str] = mapped_column(Text, nullable=False)
    skill_name: Mapped[str] = mapped_column(Text, nullable=False)
    demand_weight: Mapped[float] = mapped_column(Float, nullable=False)
    # vector(384) — must match skill_vectors.vector dimension
    vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_market_skill_reference_role_title", "role_title"),
        # ivfflat index on vector created after seed data — see database.md §5
    )


class SkillGapReport(Base):
    __tablename__ = "skill_gap_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_vector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_vectors.id", ondelete="RESTRICT"), nullable=False
    )
    target_role: Mapped[str] = mapped_column(Text, nullable=False)
    missing_skills: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="skill_gap_reports")
    skill_vector: Mapped["SkillVector"] = relationship("SkillVector", back_populates="skill_gap_reports")
    roadmap: Mapped["Roadmap | None"] = relationship("Roadmap", back_populates="skill_gap_report", uselist=False)

    __table_args__ = (
        Index("ix_skill_gap_reports_user_id", "user_id"),
    )
