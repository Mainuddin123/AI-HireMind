
import re

from backend.services.resume_parser import SKILL_DICTIONARY


# ============================================================
# REQUIREMENT CLASSIFICATION
# ============================================================

MANDATORY_TERMS = [
    "must have",
    "must possess",
    "mandatory",
    "required",
    "requirement",
    "essential",
    "minimum requirement",
    "strong knowledge of",
    "proficiency in",
    "proficient in",
    "experience with",
    "knowledge of",
    "skilled in",
]

PREFERRED_TERMS = [
    "preferred",
    "good to have",
    "nice to have",
    "desirable",
    "bonus",
    "advantage",
    "plus",
    "preferred qualification",
]

# ============================================================
# SECTION DEFINITIONS
# ============================================================

RESPONSIBILITY_HEADINGS = [
    "responsibilities",
    "key responsibilities",
    "job responsibilities",
    "what you will do",
    "what you'll do",
    "role and responsibilities",
    "duties",
    "key duties",
]

SECTION_STOP_HEADINGS = [
    "requirements",
    "qualifications",
    "preferred qualifications",
    "preferred skills",
    "education",
    "experience",
    "benefits",
    "about us",
    "about the company",
    "what we offer",
]

# ============================================================
# COMPETENCIES AND EDUCATION
# ============================================================

COMPETENCY_KEYWORDS = [
    "problem solving",
    "communication",
    "teamwork",
    "leadership",
    "analytical thinking",
    "critical thinking",
    "time management",
    "adaptability",
    "collaboration",
    "attention to detail",
    "decision making",
    "project management",
]

EDUCATION_KEYWORDS = [
    "b.tech",
    "b.e.",
    "b.sc",
    "bca",
    "mca",
    "m.tech",
    "bachelor's degree",
    "bachelor degree",
    "master's degree",
    "master degree",
    "computer science",
    "information technology",
    "artificial intelligence",
    "data science",
    "related field",
]


# ============================================================
# TEXT UTILITIES
# ============================================================

def _contains_skill(text: str, skill: str) -> bool:
    pattern = (
        r"(?<![a-zA-Z0-9+#.])"
        + re.escape(skill)
        + r"(?![a-zA-Z0-9+#.])"
    )

    return bool(re.search(pattern, text, re.IGNORECASE))


def _get_skill_aliases() -> list[str]:
    """
    Supports dictionary-style and list-style skill catalogs.
    """

    if isinstance(SKILL_DICTIONARY, dict):
        return list(SKILL_DICTIONARY.keys())

    return list(SKILL_DICTIONARY)


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience_requirement(text: str) -> float | None:

    normalized = text.lower()

    if re.search(
        r"\bfresh graduates?\b"
        r"|\brecent graduates?\b"
        r"|\bentry[- ]level\b",
        normalized,
    ):
        return 0.0

    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:to|-)\s*\d+(?:\.\d+)?"
        r"\s*years?\s+of\s+experience",

        r"(\d+(?:\.\d+)?)\+?\s*years?"
        r"\s+of\s+experience",

        r"minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\+?\s*years?",

        r"at\s+least\s+(\d+(?:\.\d+)?)\s*years?",
    ]

    for pattern in patterns:

        match = re.search(pattern, normalized)

        if match:
            return float(match.group(1))

    return None


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text: str) -> tuple[list[str], list[str]]:

    mandatory = set()
    preferred = set()

    normalized_text = text.lower()

    skills = _get_skill_aliases()

    for skill in skills:

        if not _contains_skill(normalized_text, skill):
            continue

        pattern = (
            r"(?<![a-zA-Z0-9+#.])"
            + re.escape(skill)
            + r"(?![a-zA-Z0-9+#.])"
        )

        positions = [
            match.start()
            for match in re.finditer(pattern, normalized_text)
        ]

        for position in positions:

            context = normalized_text[
                max(0, position - 250):
                min(
                    len(normalized_text),
                    position + len(skill) + 100
                )
            ]

            preferred_position = max(
                [
                    context.rfind(term)
                    for term in PREFERRED_TERMS
                ],
                default=-1,
            )

            mandatory_position = max(
                [
                    context.rfind(term)
                    for term in MANDATORY_TERMS
                ],
                default=-1,
            )

            if preferred_position > mandatory_position:
                preferred.add(skill)

            elif mandatory_position >= 0:
                mandatory.add(skill)

    # Remove duplicate classification.
    preferred = preferred - mandatory

    return sorted(mandatory), sorted(preferred)


# ============================================================
# RESPONSIBILITY EXTRACTION
# ============================================================

def extract_responsibilities(text: str) -> list[str]:

    section_pattern = (
        r"(?:responsibilities|key responsibilities|"
        r"job responsibilities|what you will do|"
        r"what you'll do|role and responsibilities|"
        r"key duties|duties)"
        r"\s*(?::|-|include|includes|are)?\s*"
        r"(.*?)"
        r"(?=\b(?:requirements|qualifications|"
        r"preferred qualifications|preferred skills|"
        r"education|experience|benefits|what we offer)\b|$)"
    )

    match = re.search(
        section_pattern,
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return []

    section = match.group(1).strip()

    # Split paragraphs, bullets and sentences.
    items = re.split(
        r"[\n•;]+|(?<=[.!?])\s+",
        section,
    )

    responsibilities = []

    action_verbs = (
        "develop",
        "build",
        "design",
        "create",
        "maintain",
        "implement",
        "analyze",
        "analyse",
        "manage",
        "support",
        "collaborate",
        "integrate",
        "test",
        "deploy",
        "monitor",
        "optimize",
        "optimise",
        "write",
        "debug",
        "work with",
        "participate",
        "assist",
        "deliver",
        "research",
    )

    for item in items:

        item = re.sub(
            r"^[\s\-*•\d.)]+",
            "",
            item,
        ).strip()

        if len(item) < 15:
            continue

        if item.lower().startswith(action_verbs):
            responsibilities.append(item[:500])

    return list(dict.fromkeys(responsibilities))[:20]


# ============================================================
# COMPETENCY EXTRACTION
# ============================================================

def extract_competencies(text: str) -> list[str]:

    normalized_text = text.lower()

    return sorted({
        competency
        for competency in COMPETENCY_KEYWORDS
        if competency in normalized_text
    })


# ============================================================
# EDUCATION EXTRACTION
# ============================================================

def extract_education_requirements(text: str) -> list[str]:

    normalized_text = text.lower()

    return sorted({
        education
        for education in EDUCATION_KEYWORDS
        if education in normalized_text
    })


# ============================================================
# MAIN JOB DESCRIPTION ANALYZER
# ============================================================

def analyze_job_description(
    job_title: str,
    description: str
) -> dict:

    if not job_title or not job_title.strip():
        raise ValueError("Job title cannot be empty.")

    if not description or not description.strip():
        raise ValueError("Job description cannot be empty.")

    mandatory, preferred = extract_skills(description)

    return {
        "job_title": job_title.strip(),

        "mandatory_skills": mandatory,

        "preferred_skills": preferred,

        "responsibilities": extract_responsibilities(description),

        "experience_years": extract_experience_requirement(
            description
        ),

        "competencies": extract_competencies(description),

        "education": extract_education_requirements(description),

        "extracted_text_length": len(description),

        "analysis_method": (
            "Enhanced deterministic keyword and pattern extraction"
        ),
    }
