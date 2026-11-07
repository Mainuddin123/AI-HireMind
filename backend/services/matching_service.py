def normalize_skills(skills: list[str]) -> set[str]:
    return {
        skill.strip().lower()
        for skill in skills
        if skill and skill.strip()
    }


def calculate_coverage(
    candidate_skills: set[str],
    job_skills: set[str]
) -> tuple[list[str], list[str], float | None]:

    if not job_skills:
        return [], [], None

    matched = sorted(candidate_skills.intersection(job_skills))
    missing = sorted(job_skills.difference(candidate_skills))

    coverage = (len(matched) / len(job_skills)) * 100

    return matched, missing, round(coverage, 2)


def calculate_experience_score(
    candidate_years: float | None,
    required_years: float | None
) -> float | None:

    if required_years is None:
        return None

    if candidate_years is None:
        return None

    if required_years == 0:
        return 100.0

    return round(
        min(candidate_years / required_years, 1.0) * 100,
        2
    )


def interpret_score(score: float) -> str:
    if score >= 80:
        return "Strong alignment"
    elif score >= 60:
        return "Moderate alignment"
    elif score >= 40:
        return "Partial alignment"
    else:
        return "Limited evidenced alignment"


def calculate_matching_score(
    mandatory_coverage: float | None,
    preferred_coverage: float | None,
    experience_score: float | None
) -> tuple[float, dict]:

    # Initial configurable weights.
    # These are prototype weights, not empirically validated.
    components = []

    if mandatory_coverage is not None:
        components.append((mandatory_coverage, 70))

    if preferred_coverage is not None:
        components.append((preferred_coverage, 20))

    if experience_score is not None:
        components.append((experience_score, 10))

    if not components:
        return 0.0, {
            "mandatory_skills": None,
            "preferred_skills": None,
            "experience": None
        }

    total_weight = sum(weight for _, weight in components)

    score = sum(
        value * weight
        for value, weight in components
    ) / total_weight

    breakdown = {
        "mandatory_skills": mandatory_coverage,
        "preferred_skills": preferred_coverage,
        "experience": experience_score
    }

    return round(score, 2), breakdown


def analyze_match(
    candidate_skills: list[str],
    candidate_experience_years: float | None,
    mandatory_skills: list[str],
    preferred_skills: list[str],
    required_experience_years: float | None
) -> dict:

    candidate_set = normalize_skills(candidate_skills)
    mandatory_set = normalize_skills(mandatory_skills)
    preferred_set = normalize_skills(preferred_skills)

    matched_mandatory, missing_mandatory, mandatory_coverage = (
        calculate_coverage(candidate_set, mandatory_set)
    )

    matched_preferred, missing_preferred, preferred_coverage = (
        calculate_coverage(candidate_set, preferred_set)
    )

    experience_score = calculate_experience_score(
        candidate_experience_years,
        required_experience_years
    )

    matching_score, breakdown = calculate_matching_score(
        mandatory_coverage,
        preferred_coverage,
        experience_score
    )

    supplied_components = [
        mandatory_coverage is not None,
        preferred_coverage is not None,
        experience_score is not None
    ]

    completeness_percentage = (
        sum(supplied_components) / len(supplied_components)
    ) * 100

    if completeness_percentage >= 100:
        completeness = "Complete"
    elif completeness_percentage >= 50:
        completeness = "Partial"
    else:
        completeness = "Limited"

    explanation = []

    if mandatory_coverage is not None:
        explanation.append(
            f"Mandatory skill coverage: {mandatory_coverage}%."
        )

    if preferred_coverage is not None:
        explanation.append(
            f"Preferred skill coverage: {preferred_coverage}%."
        )

    if experience_score is not None:
        explanation.append(
            f"Experience alignment: {experience_score}%."
        )
    elif required_experience_years is not None:
        explanation.append(
            "Experience alignment could not be calculated because "
            "candidate experience was not supplied."
        )

    if missing_mandatory:
        explanation.append(
            "Some mandatory skills were not evidenced in the "
            "supplied candidate skill list."
        )

    if not mandatory_set:
        explanation.append(
            "No mandatory skills were supplied; the score does not "
            "include mandatory skill coverage."
        )

    return {
        "matching_score": matching_score,
        "score_interpretation": interpret_score(matching_score),

        "matched_mandatory_skills": matched_mandatory,
        "missing_mandatory_skills": missing_mandatory,

        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,

        "experience_score": experience_score,
        "candidate_experience_years": candidate_experience_years,
        "required_experience_years": required_experience_years,

        "score_breakdown": breakdown,
        "evidence_completeness": completeness,
        "explanation": explanation,

        "disclaimer": (
            "This is a prototype evidence-alignment score based only "
            "on supplied information. A missing skill means it was "
            "not evidenced in the supplied data; it does not prove "
            "the candidate lacks that skill. This score must not be "
            "used as an autonomous hiring decision."
        )
    }
