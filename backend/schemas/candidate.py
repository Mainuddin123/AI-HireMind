
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Candidate registration request
class CandidateCreate(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=150
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    location: str | None = Field(
        default=None,
        max_length=150
    )


# Candidate response
class CandidateResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    location: str | None
    resume_path: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
