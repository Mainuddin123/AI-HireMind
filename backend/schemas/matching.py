from pydantic import BaseModel, Field


class MatchingRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    candidate_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60
    )

    mandatory_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)

    required_experience_years: float | None = Field(
        default=None,
        ge=0,
        le=60
    )


class MatchingResponse(BaseModel):
    matching_score: float
    score_interpretation: str

    matched_mandatory_skills: list[str]
    missing_mandatory_skills: list[str]

    matched_preferred_skills: list[str]
    missing_preferred_skills: list[str]

    experience_score: float | None
    candidate_experience_years: float | None
    required_experience_years: float | None

    score_breakdown: dict[str, float | None]
    evidence_completeness: str
    explanation: list[str]

    disclaimer: str
