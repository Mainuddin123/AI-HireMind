
from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    job_title: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    description: str = Field(
        ...,
        min_length=50,
        max_length=30000
    )


class JobDescriptionAnalysisResponse(BaseModel):
    job_title: str

    mandatory_skills: list[str] = Field(default_factory=list)

    preferred_skills: list[str] = Field(default_factory=list)

    responsibilities: list[str] = Field(default_factory=list)

    experience_years: float | None = None

    competencies: list[str] = Field(default_factory=list)

    education: list[str] = Field(default_factory=list)

    extracted_text_length: int

    analysis_method: str
