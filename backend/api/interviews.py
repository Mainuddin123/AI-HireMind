from fastapi import APIRouter, Depends, HTTPException

from backend.authentication.dependencies import get_current_user
from backend.schemas.interview import (
    InterviewPlanRequest,
    InterviewPlanResponse
)
from backend.services.interview_service import generate_interview_plan


router = APIRouter(prefix="/interviews", tags=["Interview Intelligence"])


@router.post("/generate", response_model=InterviewPlanResponse)
def create_interview_plan(
    request: InterviewPlanRequest,
    current_user=Depends(get_current_user)
):
    if current_user.role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Recruiter or admin access required."
        )

    try:
        result = generate_interview_plan(
            job_title=request.job_title,
            job_description=request.job_description,
            candidate_skills=request.candidate_skills,
            candidate_evidence=request.candidate_evidence,
            difficulty=request.difficulty,
            question_count=request.question_count
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Interview plan generation failed. Check server logs."
        )

    return {
        "job_title": request.job_title,
        "questions": result["questions"],
        "evaluation_guidance": result["evaluation_guidance"],
        "human_review_required": True
    }
