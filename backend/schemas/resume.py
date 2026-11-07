
from pydantic import BaseModel, Field


# --------------------------------------------------
# CANDIDATE RESUME UPLOAD RESPONSE
# --------------------------------------------------

class ResumeAnalysisResponse(BaseModel):
    message: str
    candidate_id: int
    filename: str
    extracted_text_length: int

    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: list[str] = Field(default_factory=list)

    resume_path: str


# --------------------------------------------------
# RECRUITER RESUME UPLOAD RESPONSE
# AUTOMATIC CANDIDATE DETAIL EXTRACTION
# --------------------------------------------------

class RecruiterResumeUploadResponse(BaseModel):
    message: str
    candidate_id: int

    # Automatically extracted candidate information
    full_name: str
    candidate_email: str
    phone: str | None = None
    location: str | None = None

    # Resume information
    filename: str
    extracted_text: str
    extracted_text_length: int

    # Resume intelligence
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = None
    education: list[str] = Field(default_factory=list)
