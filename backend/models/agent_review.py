from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class AgentReview(Base):
    __tablename__ = "agent_reviews"

    __table_args__ = (
        CheckConstraint(
            "decision IN ('approved', 'rejected')",
            name="ck_agent_review_decision"
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_agent_review_status"
        ),
        UniqueConstraint(
            "thread_id",
            "reviewer_id",
            name="uq_agent_review_thread_reviewer"
        ),
        Index(
            "ix_agent_review_thread_reviewer",
            "thread_id",
            "reviewer_id"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    reviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    thread_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending"
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )