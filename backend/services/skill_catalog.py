SKILL_ALIASES = {
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "pytorch": "pytorch",
    "py torch": "pytorch",
    "js": "javascript",
    "node": "node.js",
    "postgres": "postgresql",
    "powerbi": "power bi",
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "llms": "llm",
    "lang graph": "langgraph",
    "restful api": "rest api"
}


def normalize_skill(skill: str) -> str:
    normalized = " ".join(skill.strip().lower().split())

    return SKILL_ALIASES.get(normalized, normalized)


def normalize_skill_list(skills: list[str]) -> list[str]:
    return sorted({
        normalize_skill(skill)
        for skill in skills
        if skill and skill.strip()
    })
