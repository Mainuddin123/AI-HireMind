from typing import Any
from pydantic import BaseModel, Field


class InterviewPlanRequest(BaseModel):
    job_title: str = Field(min_length=2, max_length=150)
    job_description: str = Field(min_length=30, max_length=20000)
    candidate_skills: list[str] = Field(default_factory=list, max_length=100)
    candidate_evidence: list[str] = Field(default_factory=list, max_length=50)
    difficulty: str = Field(
        default="intermediate",
        pattern="^(beginner|intermediate|advanced)$"
    )
    question_count: int = Field(default=10, ge=5, le=20)


class InterviewPlanResponse(BaseModel):
    job_title: str
    questions: list[dict[str, Any]]
    evaluation_guidance: dict[str, Any]
    human_review_required: bool
