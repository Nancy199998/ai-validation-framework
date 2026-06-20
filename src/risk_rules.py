# src/risk_rules.py
# Combines metric evidence + governance evidence into a final validation conclusion.
# This is where the blog post argument lives:
#   Strong metrics alone are not enough — governance determines assurance.

from __future__ import annotations

# ---------------------------------------------------------------------------
# Conclusion constants
# ---------------------------------------------------------------------------
NOT_ACCEPTABLE          = "Not Acceptable"
CONDITIONAL_REVIEW      = "Conditional — Review Required"
ACCEPTABLE_CONDITIONS   = "Acceptable with Conditions"


def derive_conclusion(
    metric_summary: dict,
    governance_result: dict,
) -> dict:
    """
    Apply risk-based rules to derive a validation conclusion.

    Args:
        metric_summary:     Output of evidence_mapper.summarise_metric_evidence()
        governance_result:  Output of governance_checker.run_governance_checks()

    Returns:
        {
            "conclusion":   str,
            "rationale":    str,
            "rule_applied": str,
            "required_actions": list[str],
        }
    """
    use_case_risk    = governance_result.get("use_case_risk", "High")
    critical_fail    = governance_result.get("critical_fail", False)
    gov_status       = governance_result.get("overall_status", "Fail")
    metric_status    = metric_summary.get("overall_metric_status", "Unsatisfactory")
    gaps             = governance_result.get("gaps", [])

    # ------------------------------------------------------------------
    # Rule 1: Any unapproved or superseded source document → NOT ACCEPTABLE
    # This rule fires regardless of metric scores.
    # This is the T002 moment: good metrics, bad sources → still fails.
    # ------------------------------------------------------------------
    doc_control = next(
        (c for c in governance_result.get("controls", []) if c["control"] == "Source Documents"),
        None,
    )
    if doc_control and not doc_control["pass"]:
        return {
            "conclusion":   NOT_ACCEPTABLE,
            "rationale": (
                "One or more source documents are superseded or unapproved. "
                "Metric scores — however strong — cannot provide assurance when the "
                "knowledge corpus is not authoritative. Evaluation evidence generated "
                "against an unapproved corpus does not constitute valid validation. "
                "The system must not be deployed or continued in production."
            ),
            "rule_applied": "Rule 1: Unapproved/superseded source documents → Not Acceptable",
            "required_actions": [
                "Replace all source documents with approved, current versions.",
                "Rebuild vector store from approved corpus.",
                "Re-run full evaluation suite after corpus replacement.",
                "Submit for re-validation before any deployment or continued use.",
            ],
        }

    # ------------------------------------------------------------------
    # Rule 2: High-risk use case + any governance gap → NOT ACCEPTABLE
    # ------------------------------------------------------------------
    if use_case_risk == "High" and gov_status in ("Fail", "Conditional") and critical_fail:
        return {
            "conclusion":   NOT_ACCEPTABLE,
            "rationale": (
                f"This is a high-risk use case ({use_case_risk}) with critical governance gaps. "
                "High-risk AI systems require full governance controls to be in place before "
                "deployment. The identified gaps represent an unacceptable risk exposure."
            ),
            "rule_applied": "Rule 2: High-risk use case + critical governance gap → Not Acceptable",
            "required_actions": _gap_actions(gaps),
        }

    # ------------------------------------------------------------------
    # Rule 3: Strong metrics but governance gaps → CONDITIONAL REVIEW
    # ------------------------------------------------------------------
    if metric_status in ("Satisfactory", "Marginal") and gov_status == "Conditional":
        return {
            "conclusion":   CONDITIONAL_REVIEW,
            "rationale": (
                f"Metric evidence is {metric_status.lower()}, indicating the system performs "
                "adequately on the evaluation set. However, governance gaps remain. "
                "Assurance cannot be sustained without the controls needed to detect "
                "degradation, manage changes, and trigger revalidation."
            ),
            "rule_applied": "Rule 3: Adequate metrics + governance gaps → Conditional Review Required",
            "required_actions": _gap_actions(gaps),
        }

    # ------------------------------------------------------------------
    # Rule 4: Metrics satisfactory or marginal + all governance pass → ACCEPTABLE WITH CONDITIONS
    # No AI system is unconditionally acceptable — ongoing monitoring always required.
    # ------------------------------------------------------------------
    if metric_status in ("Satisfactory", "Marginal") and gov_status == "Pass":
        revalidation_triggers = next(
            (c.get("triggers", []) for c in governance_result.get("controls", [])
             if c["control"] == "Revalidation"),
            [],
        )
        return {
            "conclusion":   ACCEPTABLE_CONDITIONS,
            "rationale": (
                "Metric evidence is satisfactory or marginal across validation questions — "
                "no metric fell below the unsatisfactory threshold. "
                "Governance controls are in place and verified. The system may be "
                "deployed subject to the conditions listed. Ongoing monitoring and "
                "adherence to the revalidation schedule are mandatory."
            ),
            "rule_applied": "Rule 4: Satisfactory/Marginal metrics + full governance → Acceptable with Conditions",
            "required_actions": _standard_conditions(
                governance_result.get("yaml_summary", {}).get("conditions", []),
                revalidation_triggers,
            ),
        }

    # ------------------------------------------------------------------
    # Fallback: anything not caught above → CONDITIONAL REVIEW
    # ------------------------------------------------------------------
    return {
        "conclusion":   CONDITIONAL_REVIEW,
        "rationale": (
            f"Metric status is {metric_status} and governance status is {gov_status}. "
            "The combination does not meet the threshold for acceptable deployment "
            "and requires further review."
        ),
        "rule_applied": "Rule 5: Fallback — Conditional Review Required",
        "required_actions": _gap_actions(gaps),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gap_actions(gaps: list[str]) -> list[str]:
    """Convert governance gap findings into required action statements."""
    actions = []
    for gap in gaps:
        actions.append(f"Remediate: {gap}")
    actions.append("Re-submit for validation after all gaps are resolved.")
    return actions


def _standard_conditions(yaml_conditions: list[str], triggers: list[str]) -> list[str]:
    """Build required actions list for an acceptable-with-conditions outcome."""
    actions = list(yaml_conditions) if yaml_conditions else [
        "Maintain all governance controls as assessed.",
        "Continue monitoring per defined schedule.",
        "Conduct revalidation per defined triggers and schedule.",
    ]
    if triggers:
        actions.append(
            "Revalidation is required upon any of the following: "
            + "; ".join(triggers) + "."
        )
    return actions


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.evidence_mapper import map_evidence, summarise_metric_evidence
    from src.governance_checker import run_governance_checks

    test_cases = {
        "T001": {
            "faithfulness": 0.6237, "answer_relevancy": 0.9090,
            "context_recall": 0.6265, "context_precision": 0.5789,
        },
        "T002": {
            "faithfulness": 0.70, "answer_relevancy": 0.874,
            "context_recall": 0.625, "context_precision": 0.5579,
        },
        "T003": {
            "faithfulness": 0.9075, "answer_relevancy": 0.965,
            "context_recall": 0.8875, "context_precision": 0.6425,
        },
    }

    for scenario_id, scores in test_cases.items():
        evidence         = map_evidence(scores)
        metric_summary   = summarise_metric_evidence(evidence)
        governance       = run_governance_checks(scenario_id)
        result           = derive_conclusion(metric_summary, governance)

        print(f"\n{'='*60}")
        print(f"Scenario  : {scenario_id}")
        print(f"Metrics   : {metric_summary['overall_metric_status']}")
        print(f"Governance: {governance['overall_status']}")
        print(f"CONCLUSION: {result['conclusion']}")
        print(f"Rule      : {result['rule_applied']}")
        print("Actions:")
        for a in result["required_actions"]:
            print(f"  - {a}")
