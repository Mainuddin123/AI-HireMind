from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class AgenticEvaluationRequest(BaseModel):
    job_title: str = Field(
        min_length=2,
        max_length=150
    )

    resume_text: str = Field(
        min_length=20,
        max_length=50000
    )

    job_description: str = Field(
        min_length=50,
        max_length=30000
    )

    candidate_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60
    )

    thread_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )


class AgenticEvaluationResponse(BaseModel):
    thread_id: str
    status: str
    analysis: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    thread_id: str = Field(
        min_length=1,
        max_length=100
    )

    approved: bool

    comment: str = Field(
        default="",
        max_length=2000
    )


class MemoryCreateRequest(BaseModel):
    memory_type: str = Field(
        default="recruiter_preference",
        pattern="^(recruiter_preference|approved_knowledge)$"
    )

    memory_key: str = Field(
        min_length=1,
        max_length=150
    )

    memory_value: dict[str, Any]


class MemoryResponse(BaseModel):
    memory_type: str
    memory_key: str
    memory_value: dict[str, Any]