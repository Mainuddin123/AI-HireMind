from backend.services.skill_catalog import normalize_skill_list
from backend.services.skill_graph import find_related_skills


def analyze_skill_intelligence(
    candidate_skills: list[str],
    required_skills: list[str]
) -> dict:

    candidate_normalized = normalize_skill_list(candidate_skills)
    required_normalized = normalize_skill_list(required_skills)

    candidate_set = set(candidate_normalized)

    direct_matches = sorted(
        candidate_set.intersection(required_normalized)
    )

    missing_skills = sorted(
        set(required_normalized).difference(candidate_set)
    )

    transferable = {}

    for missing_skill in missing_skills:
        related = set()

        for candidate_skill in candidate_normalized:
            related_skills = find_related_skills(candidate_skill)

            if missing_skill in related_skills:
                related.add(candidate_skill)

        if related:
            transferable[missing_skill] = sorted(related)

    directly_matched_count = len(direct_matches)
    required_count = len(required_normalized)

    if required_count:
        direct_coverage = round(
            directly_matched_count / required_count * 100,
            2
        )
    else:
        direct_coverage = None

    return {
        "normalized_candidate_skills": candidate_normalized,
        "normalized_required_skills": required_normalized,
        "direct_matches": direct_matches,
        "missing_skills": missing_skills,
        "potential_transferable_skills": transferable,
        "direct_skill_coverage": direct_coverage,
        "required_skill_count": required_count,
        "matched_skill_count": directly_matched_count,
        "interpretation": (
            "Direct matches are based on normalized skill names. "
            "Transferable skills are graph-based suggestions only "
            "and require independent evidence or human review."
        )
    }
