from pydantic import BaseModel, Field


class RecruitmentEvaluationRequest(BaseModel):
    candidate_resume_text: str = Field(
        ...,
        min_length=20,
        max_length=50000
    )

    job_title: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    job_description: str = Field(
        ...,
        min_length=50,
        max_length=30000
    )

    candidate_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60
    )


class RecruitmentEvaluationResponse(BaseModel):
    candidate_analysis: dict
    job_analysis: dict
    skill_intelligence: dict
    matching_analysis: dict

    workflow_status: str
    disclaimer: str
