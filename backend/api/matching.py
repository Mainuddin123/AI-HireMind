from fastapi import APIRouter, Depends, HTTPException

from backend.authentication.dependencies import get_current_user
from backend.schemas.matching import (
    MatchingRequest,
    MatchingResponse
)
from backend.services.matching_service import analyze_match


router = APIRouter(
    prefix="/matching",
    tags=["Candidate Job Matching"]
)


@router.post(
    "/analyze",
    response_model=MatchingResponse
)
def analyze_candidate_job_match(
    request: MatchingRequest,
    current_user=Depends(get_current_user)
):
    role = getattr(current_user.role, "value", current_user.role)

    if role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only recruiters and admins can analyze candidate-job matches."
        )

    if (
        not request.mandatory_skills
        and not request.preferred_skills
        and request.required_experience_years is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide at least one job requirement."
        )

    result = analyze_match(
        candidate_skills=request.candidate_skills,
        candidate_experience_years=request.candidate_experience_years,
        mandatory_skills=request.mandatory_skills,
        preferred_skills=request.preferred_skills,
        required_experience_years=request.required_experience_years
    )

    return result
