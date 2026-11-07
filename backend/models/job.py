
from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    recruiter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    company_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    required_skills: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )

    preferred_skills: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    experience_required: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    location: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
