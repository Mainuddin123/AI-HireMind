from datetime import datetime

from sqlalchemy import (
    Integer, String, JSON, DateTime, ForeignKey,
    UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "memory_type", "memory_key",
            name="uq_agent_memory_user_type_key"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_key: Mapped[str] = mapped_column(String(150), nullable=False)
    memory_value: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return (
            f"<AgentMemory(id={self.id}, user_id={self.user_id}, "
            f"type={self.memory_type}, key={self.memory_key})>"
        )
