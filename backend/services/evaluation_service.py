from backend.services.resume_parser import analyze_resume
from backend.services.job_description_parser import (
    analyze_job_description
)
from backend.services.skill_intelligence import (
    analyze_skill_intelligence
)
from backend.services.matching_service import analyze_match


def evaluate_candidate(
    candidate_resume_text: str,
    job_title: str,
    job_description: str,
    candidate_experience_years: float | None = None
) -> dict:

    # STEP 1: Analyze candidate resume.
    candidate_analysis = analyze_resume(candidate_resume_text)

    # STEP 2: Analyze job description.
    job_analysis = analyze_job_description(
        job_title=job_title,
        description=job_description
    )

    # STEP 3: Use extracted experience unless explicitly supplied.
    experience = (
        candidate_experience_years
        if candidate_experience_years is not None
        else candidate_analysis["experience_years"]
    )

    # STEP 4: Combine job skills for skill intelligence.
    required_skills = sorted(set(
        job_analysis["mandatory_skills"]
        + job_analysis["preferred_skills"]
    ))

    # STEP 5: Analyze direct and potential transferable skills.
    skill_analysis = analyze_skill_intelligence(
        candidate_skills=candidate_analysis["skills"],
        required_skills=required_skills
    )

    # STEP 6: Calculate evidence-based matching score.
    matching_analysis = analyze_match(
        candidate_skills=candidate_analysis["skills"],
        candidate_experience_years=experience,
        mandatory_skills=job_analysis["mandatory_skills"],
        preferred_skills=job_analysis["preferred_skills"],
        required_experience_years=job_analysis["experience_years"]
    )

    # STEP 7: Return consolidated result.
    return {
        "candidate_analysis": {
            "extracted_skills": candidate_analysis["skills"],
            "experience_years": experience,
            "education": candidate_analysis["education"]
        },

        "job_analysis": job_analysis,

        "skill_intelligence": skill_analysis,

        "matching_analysis": matching_analysis,

        "workflow_status": "completed",

        "disclaimer": (
            "This report is a preliminary decision-support assessment. "
            "It relies on text extraction and deterministic rules. "
            "Missing resume evidence does not prove a candidate lacks "
            "a skill. Potential transferable skills are suggestions, "
            "not verified competencies. The score is not empirically "
            "validated and must not determine hiring outcomes. "
            "Human review is required."
        )
    }
