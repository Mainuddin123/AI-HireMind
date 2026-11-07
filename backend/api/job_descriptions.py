from fastapi import APIRouter, Depends, HTTPException

from backend.authentication.dependencies import get_current_user
from backend.schemas.job_description import (
    JobDescriptionRequest,
    JobDescriptionAnalysisResponse
)
from backend.services.job_description_parser import (
    analyze_job_description
)


router = APIRouter(
    prefix="/job-descriptions",
    tags=["Job Description Intelligence"]
)


@router.post(
    "/analyze",
    response_model=JobDescriptionAnalysisResponse
)
def analyze_description(
    request: JobDescriptionRequest,
    current_user=Depends(get_current_user)
):
    role = getattr(current_user.role, "value", current_user.role)

    if role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only recruiters and admins can analyze job descriptions."
        )

    return analyze_job_description(
        job_title=request.job_title,
        description=request.description
    )
