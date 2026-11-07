from typing import TypedDict


class RecruitmentState(TypedDict, total=False):

    # User and workflow
    user_id: int
    thread_id: str

    # Input data
    resume_text: str
    job_title: str
    job_description: str
    candidate_experience_years: float | None

    # Guardrails and memory
    guardrail_warnings: list[str]
    recruiter_memories: list[dict]

    # Agent reliability and fallback tracking
    agent_warnings: list[str]
    generation_methods: dict[str, str]

    # Resume analysis
    candidate_analysis: dict
    resume_skills: list[str]
    resume_skill_evidence: list[dict]

    # Job description analysis
    job_analysis: dict
    job_skills: list[str]
    job_skill_evidence: list[dict]

    # Skill intelligence
    skill_intelligence: dict

    # Matching
    matching_analysis: dict
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: float

    # Consolidated evaluation
    evaluation_report: dict
    analysis: dict

    # Human review
    approval_status: str
    reviewer_id: int
    reviewer_comment: str

    # Errors
    errors: list[str]