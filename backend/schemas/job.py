
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company_name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=20)

    required_skills: list[str] = Field(min_length=1)
    preferred_skills: list[str] = Field(default_factory=list)

    experience_required: int = Field(default=0, ge=0, le=60)

    location: str = Field(min_length=2, max_length=150)
    employment_type: str = Field(min_length=2, max_length=50)


class JobResponse(BaseModel):
    id: int
    recruiter_id: int
    title: str
    company_name: str
    description: str

    required_skills: list[str]
    preferred_skills: list[str]

    experience_required: int
    location: str
    employment_type: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
