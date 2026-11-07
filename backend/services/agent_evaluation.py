from collections import Counter


def calculate_extraction_metrics(
    predicted_skills: list[str],
    expected_skills: list[str]
) -> dict:
    """
    Calculate precision, recall and F1 using exact normalized skill names.
    Use a manually reviewed ground-truth dataset for expected_skills.
    """
    predicted = {
        skill.strip().casefold()
        for skill in predicted_skills
        if skill.strip()
    }

    expected = {
        skill.strip().casefold()
        for skill in expected_skills
        if skill.strip()
    }

    true_positive = len(predicted & expected)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4)
    }


def calculate_evidence_grounding(
    extracted_items: list[dict],
    source_text: str
) -> dict:
    """
    Measures whether returned evidence excerpts occur in the source.
    This does not establish that the excerpt semantically proves a skill.
    """
    normalized_source = " ".join(source_text.casefold().split())

    total = len(extracted_items)
    grounded = 0

    for item in extracted_items:
        evidence = " ".join(
            str(item.get("evidence", "")).casefold().split()
        )

        if evidence and evidence in normalized_source:
            grounded += 1

    return {
        "total_items": total,
        "grounded_items": grounded,
        "ungrounded_items": total - grounded,
        "grounding_rate": round(grounded / total, 4) if total else 0.0
    }


def calculate_dataset_summary(results: list[dict]) -> dict:
    if not results:
        return {
            "sample_count": 0,
            "average_precision": 0.0,
            "average_recall": 0.0,
            "average_f1": 0.0
        }

    count = len(results)

    return {
        "sample_count": count,
        "average_precision": round(
            sum(item["precision"] for item in results) / count, 4
        ),
        "average_recall": round(
            sum(item["recall"] for item in results) / count, 4
        ),
        "average_f1": round(
            sum(item["f1_score"] for item in results) / count, 4
        )
    }
