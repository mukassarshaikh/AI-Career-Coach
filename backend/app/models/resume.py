import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ats_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    job_descriptions: Mapped[list["JobDescription"]] = relationship("JobDescription", back_populates="resume")
    resume_reports: Mapped[list["ResumeReport"]] = relationship("ResumeReport", back_populates="resume", cascade="all, delete-orphan")
    skill_vectors: Mapped[list["SkillVector"]] = relationship("SkillVector", back_populates="resume")

    __table_args__ = (
        Index("ix_resumes_user_id", "user_id"),
    )


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_keywords: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    resume: Mapped["Resume | None"] = relationship("Resume", back_populates="job_descriptions")
    resume_reports: Mapped[list["ResumeReport"]] = relationship("ResumeReport", back_populates="job_description")

    __table_args__ = (
        Index("ix_job_descriptions_user_id", "user_id"),
        Index("ix_job_descriptions_resume_id", "resume_id"),
    )


class ResumeReport(Base):
    __tablename__ = "resume_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False
    )
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True
    )
    ats_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    grammar_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    keyword_gaps: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="resume_reports")
    job_description: Mapped["JobDescription | None"] = relationship("JobDescription", back_populates="resume_reports")

    __table_args__ = (
        Index("ix_resume_reports_resume_id", "resume_id"),
    )
