import logging
import re

from langgraph.types import interrupt

from backend.database.connection import SessionLocal
from backend.services.agent_memory_service import get_user_memories
from backend.services.evaluation_service import evaluate_candidate

from backend.services.resume_parser import (
    analyze_resume,
    extract_skills as extract_resume_skills,
)

from backend.services.job_description_parser import (
    analyze_job_description,
    extract_skills as extract_job_skills,
)

from agents.gemini_service import (
    extract_skills_with_evidence,
    generate_evaluation_explanation,
)


logger = logging.getLogger(__name__)


# --------------------------------------------------
# COMMON HELPERS
# --------------------------------------------------

def _append_warning(state: dict, message: str) -> list[str]:
    warnings = list(state.get("agent_warnings", []))

    if message not in warnings:
        warnings.append(message)

    return warnings


def _update_generation_methods(
    state: dict,
    component: str,
    method: str
) -> dict:

    methods = dict(state.get("generation_methods", {}))
    methods[component] = method

    return methods


def _extract_local_evidence(
    text: str,
    skills: list[str]
) -> list[dict]:
    """
    Extract exact source excerpts for detected skills.

    Evidence is included only when the skill is actually
    present in the supplied source text.
    """

    evidence = []

    for skill in skills:

        if not isinstance(skill, str) or not skill.strip():
            continue

        pattern = (
            r"(?<![a-zA-Z0-9+#.])"
            + re.escape(skill)
            + r"(?![a-zA-Z0-9+#.])"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 150)

        excerpt = text[start:end].strip()

        evidence.append({
            "skill": skill,
            "evidence": excerpt,
            "source": "deterministic_text_match",
        })

    return evidence


def _clean_gemini_evidence(extracted) -> list[dict]:
    """
    Keep valid Gemini skill evidence entries.
    """

    if not isinstance(extracted, list):
        return []

    cleaned = []

    for item in extracted:

        if not isinstance(item, dict):
            continue

        skill = item.get("skill")

        if not isinstance(skill, str) or not skill.strip():
            continue

        cleaned.append(item)

    return cleaned


# --------------------------------------------------
# 1. RECRUITER MEMORY RETRIEVAL
# --------------------------------------------------

def memory_retrieval_node(state: dict) -> dict:
    """Retrieve recruiter preferences from long-term memory."""

    db = SessionLocal()

    try:
        memories = get_user_memories(
            db,
            state["user_id"],
            memory_type="recruiter_preference",
        )

        return {
            "recruiter_memories": memories or []
        }

    except Exception:
        logger.exception("Recruiter memory retrieval failed")

        return {
            "recruiter_memories": [],
            "agent_warnings": _append_warning(
                state,
                "Recruiter memory retrieval failed. "
                "Evaluation continued without stored preferences."
            ),
        }

    finally:
        db.close()


# --------------------------------------------------
# 2. RESUME ANALYSIS
# --------------------------------------------------

def resume_analysis_node(state: dict) -> dict:
    """
    Extract resume skills and supporting evidence.

    Gemini is preferred. Existing deterministic resume
    parsing is used when Gemini is unavailable.
    """

    resume_text = state.get("resume_text", "")

    try:
        extracted = extract_skills_with_evidence(resume_text)

        extracted = _clean_gemini_evidence(extracted)

        skills = list(dict.fromkeys(
            item["skill"].strip()
            for item in extracted
        ))

        if not skills and resume_text.strip():
            raise ValueError(
                "Gemini did not return valid resume skills."
            )

        return {
            "resume_skills": skills,
            "resume_skill_evidence": extracted,
            "candidate_analysis": analyze_resume(resume_text),
            "generation_methods": _update_generation_methods(
                state,
                "resume_analysis",
                "gemini"
            ),
        }

    except Exception:
        logger.exception(
            "Gemini resume analysis failed; using local parser"
        )

        candidate_analysis = analyze_resume(resume_text)

        skills = extract_resume_skills(resume_text)

        evidence = _extract_local_evidence(
            resume_text,
            skills
        )

        return {
            "candidate_analysis": candidate_analysis,
            "resume_skills": skills,
            "resume_skill_evidence": evidence,
            "agent_warnings": _append_warning(
                state,
                "Gemini resume analysis unavailable. "
                "Deterministic resume parsing was used."
            ),
            "generation_methods": _update_generation_methods(
                state,
                "resume_analysis",
                "deterministic_fallback"
            ),
        }


# --------------------------------------------------
# 3. JOB DESCRIPTION ANALYSIS
# --------------------------------------------------

def job_analysis_node(state: dict) -> dict:
    """
    Extract job skills and supporting evidence.

    Gemini is preferred. Existing deterministic job
    description parsing is used as a fallback.
    """

    job_description = state.get("job_description", "")
    job_title = state.get("job_title", "")

    try:
        extracted = extract_skills_with_evidence(
            job_description
        )

        extracted = _clean_gemini_evidence(extracted)

        skills = list(dict.fromkeys(
            item["skill"].strip()
            for item in extracted
        ))

        if not skills and job_description.strip():
            raise ValueError(
                "Gemini did not return valid job skills."
            )

        return {
            "job_skills": skills,
            "job_skill_evidence": extracted,
            "generation_methods": _update_generation_methods(
                state,
                "job_analysis",
                "gemini"
            ),
        }

    except Exception:
        logger.exception(
            "Gemini job analysis failed; using local parser"
        )

        job_analysis = analyze_job_description(
            job_title,
            job_description
        )

        mandatory = job_analysis.get(
            "mandatory_skills", []
        )

        preferred = job_analysis.get(
            "preferred_skills", []
        )

        skills = list(dict.fromkeys(
            mandatory + preferred
        ))

        evidence = _extract_local_evidence(
            job_description,
            skills
        )

        return {
            "job_analysis": job_analysis,
            "job_skills": skills,
            "job_skill_evidence": evidence,
            "agent_warnings": _append_warning(
                state,
                "Gemini job analysis unavailable. "
                "Deterministic job description parsing was used."
            ),
            "generation_methods": _update_generation_methods(
                state,
                "job_analysis",
                "deterministic_fallback"
            ),
        }


# --------------------------------------------------
# 4. DETERMINISTIC CANDIDATE EVALUATION
# --------------------------------------------------

def matching_node(state: dict) -> dict:
    """
    Execute the integrated evaluation service.

    Matching scores are calculated by the existing
    deterministic evaluation service.
    """

    try:
        report = evaluate_candidate(
            candidate_resume_text=state.get(
                "resume_text", ""
            ),
            job_title=state.get(
                "job_title", ""
            ),
            job_description=state.get(
                "job_description", ""
            ),
            candidate_experience_years=state.get(
                "candidate_experience_years"
            ),
        )

        matching = report.get(
            "matching_analysis", {}
        )

        matched_mandatory = matching.get(
            "matched_mandatory_skills", []
        )

        matched_preferred = matching.get(
            "matched_preferred_skills", []
        )

        missing_mandatory = matching.get(
            "missing_mandatory_skills", []
        )

        missing_preferred = matching.get(
            "missing_preferred_skills", []
        )

        matched = list(dict.fromkeys(
            matched_mandatory + matched_preferred
        ))

        missing = list(dict.fromkeys(
            missing_mandatory + missing_preferred
        ))

        return {
            "candidate_analysis": report.get(
                "candidate_analysis", {}
            ),

            "job_analysis": report.get(
                "job_analysis", {}
            ),

            "skill_intelligence": report.get(
                "skill_intelligence", {}
            ),

            "matching_analysis": matching,

            "evaluation_report": report,

            "matched_skills": matched,

            "missing_skills": missing,

            "match_percentage": matching.get(
                "matching_score", 0.0
            ),

            "generation_methods": _update_generation_methods(
                state,
                "matching",
                "deterministic"
            ),
        }

    except Exception:
        logger.exception("Candidate evaluation failed")
        raise


# --------------------------------------------------
# 5. EXPLANATION
# --------------------------------------------------

def _generate_local_explanation(
    matched_skills: list,
    missing_skills: list,
    match_percentage: float,
    matching_analysis: dict
) -> str:
    """
    Generate a factual explanation from deterministic
    matching results. Does not make hiring decisions.
    """

    interpretation = matching_analysis.get(
        "score_interpretation",
        "Interpretation unavailable."
    )

    matched_text = (
        ", ".join(matched_skills)
        if matched_skills
        else "No matched skills identified."
    )

    missing_text = (
        ", ".join(missing_skills)
        if missing_skills
        else "No missing skills identified."
    )

    return (
        f"Matching analysis identified {match_percentage:.2f}% "
        f"evidence alignment. The score interpretation is: "
        f"{interpretation}\n\n"
        f"Matched skills: {matched_text}\n\n"
        f"Missing skills: {missing_text}\n\n"
        "This result is decision-support information only. "
        "A recruiter must independently review the candidate's "
        "experience and supporting evidence before making "
        "a hiring decision."
    )


def explanation_node(state: dict) -> dict:
    """
    Generate an explanation using Gemini.

    Uses a deterministic explanation if Gemini is unavailable.
    Matching facts always come from the evaluation service.
    """

    matched_skills = state.get("matched_skills", [])
    missing_skills = state.get("missing_skills", [])
    match_percentage = state.get("match_percentage", 0.0)

    matching = state.get("matching_analysis", {})

    try:
        explanation = generate_evaluation_explanation(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            match_percentage=match_percentage,
        )

        if not isinstance(explanation, str) or not explanation.strip():
            raise ValueError(
                "Gemini returned an empty explanation."
            )

        method = "gemini"

    except Exception:
        logger.exception(
            "Gemini explanation failed; using local explanation"
        )

        explanation = _generate_local_explanation(
            matched_skills,
            missing_skills,
            match_percentage,
            matching,
        )

        method = "deterministic_fallback"

    evaluation_report = state.get(
        "evaluation_report", {}
    )

    analysis = {
        "candidate_analysis": state.get(
            "candidate_analysis", {}
        ),

        "job_analysis": state.get(
            "job_analysis", {}
        ),

        "skill_intelligence": state.get(
            "skill_intelligence", {}
        ),

        "matching_analysis": matching,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "match_percentage": match_percentage,

        "score_interpretation": matching.get(
            "score_interpretation", ""
        ),

        "score_breakdown": matching.get(
            "score_breakdown", {}
        ),

        "evidence_completeness": matching.get(
            "evidence_completeness", ""
        ),

        "resume_skill_evidence": state.get(
            "resume_skill_evidence", []
        ),

        "job_skill_evidence": state.get(
            "job_skill_evidence", []
        ),

        "recruiter_memory_count": len(
            state.get("recruiter_memories", [])
        ),

        "ai_explanation": explanation,

        "generation_methods": _update_generation_methods(
            state,
            "explanation",
            method
        ),

        "agent_warnings": state.get(
            "agent_warnings", []
        ),

        "guardrail_warnings": state.get(
            "guardrail_warnings", []
        ),

        "scoring_note": (
            "The matching score is a prototype evidence-alignment "
            "score calculated by the deterministic matching service. "
            "It is not an empirically validated hiring prediction."
        ),

        "human_review_required": True,

        "disclaimer": evaluation_report.get(
            "disclaimer",
            "AI evaluation is decision support only. "
            "A recruiter must make the final hiring decision."
        ),
    }

    if method == "deterministic_fallback":
        analysis["agent_warnings"] = _append_warning(
            state,
            "Gemini explanation unavailable. "
            "A deterministic explanation was generated."
        )

    return {
        "analysis": analysis,
        "generation_methods": analysis["generation_methods"],
        "agent_warnings": analysis["agent_warnings"],
    }


# --------------------------------------------------
# 6. HUMAN-IN-THE-LOOP REVIEW
# --------------------------------------------------

def human_review_node(state: dict) -> dict:
    """
    Pause until a recruiter submits an explicit decision.
    """

    review = interrupt({
        "type": "human_review_required",

        "message": (
            "Review the candidate evidence and AI analysis "
            "before recording your decision."
        ),

        "analysis": state.get("analysis", {}),
    })

    if not isinstance(review, dict):
        raise ValueError("Invalid human review response.")

    approved = review.get("approved")

    if not isinstance(approved, bool):
        raise ValueError(
            "Human review must contain a boolean approval decision."
        )

    reviewer_id = review.get("reviewer_id")

    if not isinstance(reviewer_id, int) or reviewer_id <= 0:
        raise ValueError("Valid reviewer ID is required.")

    comment = review.get("comment", "")

    if comment is not None and not isinstance(comment, str):
        raise ValueError("Review comment must be text.")

    return {
        "approval_status": (
            "approved" if approved else "rejected"
        ),

        "reviewer_id": reviewer_id,

        "reviewer_comment": comment or "",
    }