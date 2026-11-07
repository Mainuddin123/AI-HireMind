from fastapi import APIRouter, Depends, HTTPException

from backend.authentication.dependencies import get_current_user
from backend.schemas.evaluation import (
    RecruitmentEvaluationRequest,
    RecruitmentEvaluationResponse
)
from backend.services.evaluation_service import evaluate_candidate


router = APIRouter(
    prefix="/evaluation",
    tags=["Integrated Recruitment Intelligence"]
)


@router.post(
    "/analyze",
    response_model=RecruitmentEvaluationResponse
)
def run_recruitment_evaluation(
    request: RecruitmentEvaluationRequest,
    current_user=Depends(get_current_user)
):

    role = getattr(current_user.role, "value", current_user.role)

    if role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only recruiters and admins can run evaluations."
        )

    result = evaluate_candidate(
        candidate_resume_text=request.candidate_resume_text,
        job_title=request.job_title,
        job_description=request.job_description,
        candidate_experience_years=request.candidate_experience_years
    )

    return result
