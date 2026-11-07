# Manually curated relationships.
# Related skills are suggestions, not proof of competency.

SKILL_GRAPH = {
    "python": [
        "pandas",
        "numpy",
        "scikit-learn",
        "fastapi",
        "django",
        "flask"
    ],
    "machine learning": [
        "scikit-learn",
        "model evaluation",
        "feature engineering",
        "statistics"
    ],
    "deep learning": [
        "pytorch",
        "tensorflow",
        "keras",
        "neural networks"
    ],
    "data analysis": [
        "pandas",
        "numpy",
        "sql",
        "power bi",
        "tableau"
    ],
    "natural language processing": [
        "transformers",
        "llm",
        "text classification",
        "embeddings"
    ],
    "llm": [
        "rag",
        "prompt engineering",
        "embeddings",
        "langchain",
        "langgraph"
    ],
    "backend development": [
        "fastapi",
        "django",
        "flask",
        "rest api"
    ],
    "computer vision": [
        "opencv",
        "pytorch",
        "tensorflow",
        "image classification",
        "object detection"
    ],
    "sql": [
        "mysql",
        "postgresql",
        "database design"
    ],
    "cloud computing": [
        "aws",
        "azure",
        "gcp",
        "docker"
    ]
}


def find_related_skills(skill: str) -> list[str]:
    return SKILL_GRAPH.get(skill, [])


def build_skill_graph() -> dict[str, list[str]]:
    return {
        skill: sorted(set(related))
        for skill, related in SKILL_GRAPH.items()
    }
