from fastapi import APIRouter, Depends, HTTPException

from backend.authentication.dependencies import get_current_user
from backend.schemas.skill_intelligence import (
    SkillIntelligenceRequest,
    SkillIntelligenceResponse
)
from backend.services.skill_intelligence import (
    analyze_skill_intelligence
)


router = APIRouter(
    prefix="/skills",
    tags=["Skill Intelligence"]
)


@router.post(
    "/analyze",
    response_model=SkillIntelligenceResponse
)
def analyze_skills(
    request: SkillIntelligenceRequest,
    current_user=Depends(get_current_user)
):
    role = getattr(current_user.role, "value", current_user.role)

    if role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only recruiters and admins can analyze skills."
        )

    if not request.required_skills:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one required skill."
        )

    return analyze_skill_intelligence(
        candidate_skills=request.candidate_skills,
        required_skills=request.required_skills
    )
