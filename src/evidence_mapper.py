# src/evidence_mapper.py
# Maps RAGAS metric scores to validation questions and assigns rating levels.

from __future__ import annotations

METRIC_MAP = {
    "faithfulness": {
        "question": "Are outputs grounded in authoritative sources?",
        "rationale": (
            "Faithfulness measures whether the generated answer is supported by "
            "the retrieved context. Low scores indicate hallucination or unsupported claims."
        ),
    },
    "context_recall": {
        "question": "Is relevant information consistently retrieved?",
        "rationale": (
            "Context recall measures whether the retrieval pipeline surfaces the "
            "information needed to answer each question. Low scores indicate retrieval gaps."
        ),
    },
    "answer_relevancy": {
        "question": "Are responses relevant to the question asked?",
        "rationale": (
            "Answer relevancy measures whether the generated response addresses "
            "the user's question. Low scores indicate off-topic or evasive answers."
        ),
    },
    "context_precision": {
        "question": "Is retrieval focused, avoiding noise?",
        "rationale": (
            "Context precision measures whether retrieved chunks are useful rather "
            "than noisy. Low scores indicate the retriever is surfacing irrelevant content."
        ),
    },
}

THRESHOLDS = {
    "Satisfactory": 0.80,
    "Marginal":     0.60,
    # below 0.60 → Unsatisfactory
}


def rate_score(score: float) -> str:
    """Return a rating label for a single metric score."""
    if score >= THRESHOLDS["Satisfactory"]:
        return "Satisfactory"
    elif score >= THRESHOLDS["Marginal"]:
        return "Marginal"
    else:
        return "Unsatisfactory"


def map_evidence(scores: dict[str, float]) -> list[dict]:
    """
    Map a dict of metric scores to structured evidence records.

    Args:
        scores: e.g. {"faithfulness": 0.62, "answer_relevancy": 0.91, ...}

    Returns:
        List of dicts, one per metric, with keys:
            metric, question, score, rating, rationale
    """
    evidence = []
    for metric, value in scores.items():
        meta = METRIC_MAP.get(metric)
        if meta is None:
            # Pass through unknown metrics without a mapped question
            meta = {
                "question": f"[Unmapped metric: {metric}]",
                "rationale": "No validation question mapping defined for this metric.",
            }
        evidence.append(
            {
                "metric":    metric,
                "question":  meta["question"],
                "score":     round(value, 4),
                "rating":    rate_score(value),
                "rationale": meta["rationale"],
            }
        )
    return evidence


def summarise_metric_evidence(evidence: list[dict]) -> dict:
    """
    Return a high-level summary across all mapped metrics.

    Returns:
        {
            "overall_metric_status": "Satisfactory" | "Marginal" | "Unsatisfactory",
            "satisfactory_count": int,
            "marginal_count": int,
            "unsatisfactory_count": int,
            "total": int,
        }
    """
    counts = {"Satisfactory": 0, "Marginal": 0, "Unsatisfactory": 0}
    for item in evidence:
        counts[item["rating"]] += 1

    total = sum(counts.values())

    if counts["Unsatisfactory"] > 0:
        overall = "Unsatisfactory"
    elif counts["Marginal"] > 0:
        overall = "Marginal"
    else:
        overall = "Satisfactory"

    return {
        "overall_metric_status": overall,
        "satisfactory_count":    counts["Satisfactory"],
        "marginal_count":        counts["Marginal"],
        "unsatisfactory_count":  counts["Unsatisfactory"],
        "total":                 total,
    }


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_scores = {
        "faithfulness":     0.6237,
        "answer_relevancy": 0.9090,
        "context_recall":   0.6265,
        "context_precision": 0.5789,
    }

    evidence = map_evidence(sample_scores)
    summary  = summarise_metric_evidence(evidence)

    print("=== Evidence Items ===")
    for item in evidence:
        print(f"  {item['metric']:<22} {item['score']:.4f}  [{item['rating']}]")
        print(f"    Q: {item['question']}")

    print("\n=== Summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
