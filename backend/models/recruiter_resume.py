
from datetime import datetime

from sqlalchemy import (
    Integer, String, Text, Float, JSON, DateTime,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class RecruiterResume(Base):
    __tablename__ = "recruiter_resumes"

    __table_args__ = (
        UniqueConstraint(
            "recruiter_id",
            "candidate_id",
            name="uq_recruiter_candidate_resume"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    recruiter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)

    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience_years: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    education: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
