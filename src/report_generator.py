# src/report_generator.py
# Assembles metric evidence, governance evidence, and risk conclusion
# into a structured markdown validation report.

from __future__ import annotations

import csv
import os
from datetime import date
from pathlib import Path

OUTPUTS_DIR      = "outputs"
GOVERNANCE_PATH  = "data/governance_inputs.yaml"

SCENARIO_META = {
    "T001": {
        "title":       "Basic RAG — Outdated Documents — No Governance",
        "key_risks": [
            "Responses grounded in superseded regulatory guidance",
            "No mechanism to detect when source documents become outdated",
            "No human escalation path for uncertain or high-stakes queries",
            "No prompt change control — silent drift possible",
        ],
    },
    "T002": {
        "title":       "Optimized RAG — Outdated Documents — No Governance",
        "key_risks": [
            "Reranking surfaces better chunks but corpus remains superseded",
            "Strong metric scores may create false confidence in the system",
            "No governance controls in place despite improved RAG performance",
            "Demonstrates that evaluation cannot substitute for governance",
        ],
    },
    "T003": {
        "title":       "Optimized RAG — Current Documents — Full Governance",
        "key_risks": [
            "Context precision is marginal — some retrieval noise remains",
            "Ongoing risk of corpus becoming outdated as regulations evolve",
            "Continued adherence to governance controls is required",
            "Annual revalidation required to sustain assurance over time",
        ],
    },
}


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------

def load_scores_from_csv(scenario_id: str) -> dict[str, float]:
    """Read mean_score values from T00X_summary.csv into a dict."""
    path = Path(OUTPUTS_DIR) / f"{scenario_id}_summary.csv"
    scores = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("scenario") == scenario_id:
                scores[row["metric"]] = float(row["mean_score"])
    return scores


# ---------------------------------------------------------------------------
# Markdown builders
# ---------------------------------------------------------------------------

def _rating_badge(rating: str) -> str:
    badges = {
        "Satisfactory":   "✅ Satisfactory",
        "Marginal":       "⚠️  Marginal",
        "Unsatisfactory": "❌ Unsatisfactory",
    }
    return badges.get(rating, rating)


def _pass_badge(pass_flag: bool, critical: bool = False) -> str:
    if pass_flag:
        return "✅ Pass"
    return "❌ Critical Fail" if critical else "❌ Fail"


def _conclusion_badge(conclusion: str) -> str:
    badges = {
        "Not Acceptable":                "🔴 Not Acceptable",
        "Conditional — Review Required": "🟡 Conditional — Review Required",
        "Acceptable with Conditions":    "🟢 Acceptable with Conditions",
    }
    return badges.get(conclusion, conclusion)


def build_report(
    scenario_id: str,
    evidence: list[dict],
    metric_summary: dict,
    governance_result: dict,
    conclusion_result: dict,
) -> str:
    """Assemble and return the full markdown report as a string."""

    meta        = SCENARIO_META.get(scenario_id, {})
    today       = date.today().isoformat()
    title       = meta.get("title", scenario_id)
    key_risks   = meta.get("key_risks", [])
    intended_use = governance_result.get("intended_use", "Not specified")
    use_case_risk = governance_result.get("use_case_risk", "Not specified")
    label       = governance_result.get("label", "")

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        f"# Validation Report — {scenario_id}",
        f"**{title}**",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Scenario ID | {scenario_id} |",
        f"| Report Date | {today} |",
        f"| Use Case Risk | {use_case_risk} |",
        f"| Overall Conclusion | {_conclusion_badge(conclusion_result['conclusion'])} |",
        "",
        "---",
        "",
    ]

    # ── 1. Use Case Overview ─────────────────────────────────────────────────
    lines += [
        "## 1. Use Case Overview",
        "",
        f"{label}",
        "",
    ]

    # ── 2. Intended Use ──────────────────────────────────────────────────────
    lines += [
        "## 2. Intended Use",
        "",
        f"{intended_use}",
        "",
    ]

    # ── 3. Key Risks ─────────────────────────────────────────────────────────
    lines += [
        "## 3. Key Risks",
        "",
    ]
    for risk in key_risks:
        lines.append(f"- {risk}")
    lines.append("")

    # ── 4. Validation Questions ───────────────────────────────────────────────
    lines += [
        "## 4. Validation Questions",
        "",
        "| # | Validation Question | Metric | Score | Rating |",
        "|---|---------------------|--------|-------|--------|",
    ]
    for i, item in enumerate(evidence, 1):
        lines.append(
            f"| {i} | {item['question']} "
            f"| {item['metric']} "
            f"| {item['score']:.4f} "
            f"| {_rating_badge(item['rating'])} |"
        )
    lines.append("")

    # ── 5. Evaluation Evidence ────────────────────────────────────────────────
    lines += [
        "## 5. Evaluation Evidence",
        "",
        f"**Overall metric status: {metric_summary['overall_metric_status']}**",
        "",
        f"- Satisfactory: {metric_summary['satisfactory_count']} / {metric_summary['total']}",
        f"- Marginal: {metric_summary['marginal_count']} / {metric_summary['total']}",
        f"- Unsatisfactory: {metric_summary['unsatisfactory_count']} / {metric_summary['total']}",
        "",
        "> Scores generated using Gemini custom scorer via `evaluation/ragas_runner.py`.",
        "> Thresholds: ≥ 0.80 Satisfactory · 0.60–0.79 Marginal · < 0.60 Unsatisfactory",
        "",
    ]

    for item in evidence:
        lines += [
            f"### {item['metric']}",
            f"- **Score:** {item['score']:.4f} — {_rating_badge(item['rating'])}",
            f"- **Validation question:** {item['question']}",
            f"- **Rationale:** {item['rationale']}",
            "",
        ]

    # ── 6. Governance Evidence ────────────────────────────────────────────────
    lines += [
        "## 6. Governance Evidence",
        "",
        f"**Overall governance status: {governance_result['overall_status']}**",
        "",
        "| Control Area | Status | Finding |",
        "|--------------|--------|---------|",
    ]
    for c in governance_result["controls"]:
        badge = _pass_badge(c["pass"], c.get("critical", False))
        finding = c["finding"].replace("|", "\\|")   # escape pipe chars in markdown
        lines.append(f"| {c['control']} | {badge} | {finding} |")
    lines.append("")

    # Source document detail
    doc_control = next(
        (c for c in governance_result["controls"] if c["control"] == "Source Documents"), None
    )
    if doc_control and doc_control.get("sources"):
        lines += [
            "### Source Document Detail",
            "",
            "| Document | Version | Status | Approved |",
            "|----------|---------|--------|----------|",
        ]
        for s in doc_control["sources"]:
            approved = "✅ Yes" if s["approved"] else "❌ No"
            superseded = f" (superseded by {s['superseded_by']})" if s.get("superseded_by") else ""
            lines.append(
                f"| {s['name']} | {s['version']} | {s['status']}{superseded} | {approved} |"
            )
        lines.append("")

    # Gaps
    if governance_result["gaps"]:
        lines += ["### Governance Gaps Identified", ""]
        for gap in governance_result["gaps"]:
            lines.append(f"- {gap}")
        lines.append("")

    # ── 7. Validation Conclusion ──────────────────────────────────────────────
    lines += [
        "## 7. Validation Conclusion",
        "",
        f"**{_conclusion_badge(conclusion_result['conclusion'])}**",
        "",
        f"**Rule applied:** {conclusion_result['rule_applied']}",
        "",
        conclusion_result["rationale"],
        "",
    ]

    # T002 key insight
    yaml_summary = governance_result.get("yaml_summary", {})
    if "key_insight" in yaml_summary:
        lines += [
            "> **Key Insight:** " + yaml_summary["key_insight"].strip(),
            "",
        ]

    # ── 8. Required Actions ───────────────────────────────────────────────────
    lines += [
        "## 8. Required Actions",
        "",
    ]
    for i, action in enumerate(conclusion_result["required_actions"], 1):
        lines.append(f"{i}. {action}")
    lines.append("")

    # ── 9. Monitoring Recommendations ────────────────────────────────────────
    monitoring_control = next(
        (c for c in governance_result["controls"] if c["control"] == "Monitoring"), None
    )
    lines += [
        "## 9. Monitoring Recommendations",
        "",
    ]
    if monitoring_control and monitoring_control["pass"]:
        lines += [
            "The following monitoring controls are in place and should be maintained:",
            "",
            f"- {monitoring_control['notes']}",
            "- Alert on faithfulness score drop below 0.70 in production sampling.",
            "- Alert on context precision drop below 0.55.",
            "",
        ]
    else:
        lines += [
            "No monitoring controls are currently in place. The following are required:",
            "",
            "- Define and implement an output sampling process (minimum weekly).",
            "- Implement embedding drift detection (minimum monthly).",
            "- Establish alerting thresholds for faithfulness and context precision.",
            "- Assign ownership for monitoring review and escalation.",
            "",
        ]

    # ── 10. Revalidation Triggers ─────────────────────────────────────────────
    revalidation_control = next(
        (c for c in governance_result["controls"] if c["control"] == "Revalidation"), None
    )
    lines += [
        "## 10. Revalidation Triggers",
        "",
    ]
    if revalidation_control and revalidation_control.get("triggers"):
        lines.append("Revalidation is required upon any of the following:")
        lines.append("")
        for trigger in revalidation_control["triggers"]:
            lines.append(f"- {trigger}")
        lines.append("")
    else:
        lines += [
            "No revalidation triggers are currently defined. The following are recommended:",
            "",
            "- Change to foundation model provider or version",
            "- Change to retrieval corpus or source documents",
            "- Material change to prompt",
            "- Regulatory guidance update affecting the use case",
            "- Annual scheduled revalidation",
            "",
        ]

    # ── Footer ───────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        f"*Report generated by AI Validation Framework · {today}*",
        "",
    ]

    return "\n".join(lines)


def save_report(scenario_id: str, content: str) -> Path:
    """Write the report markdown to outputs/."""
    path = Path(OUTPUTS_DIR) / f"{scenario_id}_validation_report.md"
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.evidence_mapper import map_evidence, summarise_metric_evidence
    from src.governance_checker import run_governance_checks
    from src.risk_rules import derive_conclusion

    for scenario_id in ["T001", "T002", "T003"]:
        scores           = load_scores_from_csv(scenario_id)
        evidence         = map_evidence(scores)
        metric_summary   = summarise_metric_evidence(evidence)
        governance       = run_governance_checks(scenario_id)
        conclusion       = derive_conclusion(metric_summary, governance)
        report_md        = build_report(scenario_id, evidence, metric_summary, governance, conclusion)
        out_path         = save_report(scenario_id, report_md)

        print(f"[{scenario_id}] {conclusion['conclusion']} → {out_path}")
