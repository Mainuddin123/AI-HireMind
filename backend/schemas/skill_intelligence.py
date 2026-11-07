from pydantic import BaseModel, Field


class SkillIntelligenceRequest(BaseModel):
    candidate_skills: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)


class SkillIntelligenceResponse(BaseModel):
    normalized_candidate_skills: list[str]
    normalized_required_skills: list[str]
    direct_matches: list[str]
    missing_skills: list[str]
    potential_transferable_skills: dict[str, list[str]]
    direct_skill_coverage: float | None
    required_skill_count: int
    matched_skill_count: int
    interpretation: str
