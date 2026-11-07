
from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field
)


class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFERED = "offered"
    REJECTED = "rejected"


class PublicApplicationCreate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150
    )

    email: EmailStr

    phone: str = Field(
        min_length=7,
        max_length=20
    )

    location: str | None = Field(
        default=None,
        max_length=150
    )


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublicApplicationResponse(BaseModel):
    message: str
    application_id: int
    job_id: int
    status: ApplicationStatus


class RecruiterApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    created_at: datetime
    candidate_name: str
    candidate_email: EmailStr
    candidate_phone: str | None

    model_config = ConfigDict(from_attributes=True)
