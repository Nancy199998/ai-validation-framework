# src/governance_checker.py
# Reads governance_inputs.yaml for a given scenario and assesses each control.

from __future__ import annotations

import yaml
from pathlib import Path

GOVERNANCE_PATH = "data/governance_inputs.yaml"


def load_governance(path: str = GOVERNANCE_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_documents(doc_block: dict) -> dict:
    """Assess document controls. Unapproved/superseded sources are an auto-fail."""
    sources = doc_block.get("sources", [])
    all_approved = doc_block.get("all_sources_approved", False)
    all_current  = doc_block.get("all_sources_current", False)

    source_details = []
    for s in sources:
        source_details.append({
            "name":          s.get("name"),
            "version":       s.get("version"),
            "status":        s.get("status"),
            "approved":      s.get("approved", False),
            "superseded_by": s.get("superseded_by"),
            "notes":         s.get("notes"),
        })

    pass_flag = all_approved and all_current
    return {
        "control":        "Source Documents",
        "pass":           pass_flag,
        "critical":       True,          # auto-fail if False
        "all_approved":   all_approved,
        "all_current":    all_current,
        "sources":        source_details,
        "finding": (
            "All source documents are approved and current."
            if pass_flag else
            "One or more source documents are superseded or not approved for use. "
            "This is a critical governance failure — metrics cannot compensate."
        ),
    }


def check_prompt(prompt_block: dict) -> dict:
    versioned         = prompt_block.get("versioned", False)
    change_controlled = prompt_block.get("change_controlled", False)
    last_reviewed     = prompt_block.get("last_reviewed")
    notes             = prompt_block.get("notes", "")

    pass_flag = versioned and change_controlled
    return {
        "control":          "Prompt Governance",
        "pass":             pass_flag,
        "critical":         False,
        "versioned":        versioned,
        "change_controlled": change_controlled,
        "last_reviewed":    last_reviewed,
        "notes":            notes,
        "finding": (
            f"Prompt is versioned and change-controlled. Last reviewed: {last_reviewed}."
            if pass_flag else
            "Prompt is not versioned or change-controlled. "
            "Changes cannot be tracked or rolled back."
        ),
    }


def check_monitoring(monitoring_block: dict) -> dict:
    process_defined  = monitoring_block.get("process_defined", False)
    output_sampling  = monitoring_block.get("output_sampling", False)
    drift_detection  = monitoring_block.get("drift_detection", False)
    notes            = monitoring_block.get("notes", "")

    pass_flag = process_defined and output_sampling and drift_detection
    return {
        "control":          "Monitoring",
        "pass":             pass_flag,
        "critical":         False,
        "process_defined":  process_defined,
        "output_sampling":  output_sampling,
        "drift_detection":  drift_detection,
        "notes":            notes,
        "finding": (
            "Monitoring process is defined with output sampling and drift detection."
            if pass_flag else
            "No monitoring process defined. Performance degradation will go undetected."
        ),
    }


def check_escalation(escalation_block: dict) -> dict:
    path_defined = escalation_block.get("human_review_path_defined", False)
    tested       = escalation_block.get("escalation_tested", False)
    notes        = escalation_block.get("notes", "")

    pass_flag = path_defined and tested
    return {
        "control":     "Human Escalation",
        "pass":        pass_flag,
        "critical":    False,
        "path_defined": path_defined,
        "tested":      tested,
        "notes":       notes,
        "finding": (
            "Human escalation path is defined and has been tested."
            if pass_flag else
            "Human escalation path is not defined or has not been tested."
        ),
    }


def check_revalidation(revalidation_block: dict) -> dict:
    trigger_defined  = revalidation_block.get("trigger_defined", False)
    schedule_defined = revalidation_block.get("schedule_defined", False)
    triggers         = revalidation_block.get("triggers", [])
    notes            = revalidation_block.get("notes", "")

    pass_flag = trigger_defined and schedule_defined
    return {
        "control":          "Revalidation",
        "pass":             pass_flag,
        "critical":         False,
        "trigger_defined":  trigger_defined,
        "schedule_defined": schedule_defined,
        "triggers":         triggers,
        "notes":            notes,
        "finding": (
            f"Revalidation triggers and schedule are defined. Triggers: {', '.join(triggers)}."
            if pass_flag else
            "No revalidation triggers or schedule defined. "
            "There is no mechanism to detect when revalidation is required."
        ),
    }


def run_governance_checks(scenario_id: str, path: str = GOVERNANCE_PATH) -> dict:
    """
    Run all governance checks for a scenario.

    Returns:
        {
            "scenario":          str,
            "label":             str,
            "use_case_risk":     str,
            "controls":          list[dict],   # one per control area
            "critical_fail":     bool,         # True if any critical control failed
            "overall_status":    str,          # "Pass" | "Fail" | "Conditional"
            "gaps":              list[str],    # human-readable gap descriptions
            "yaml_summary":      dict,         # raw governance_summary from yaml
        }
    """
    data     = load_governance(path)
    scenario = data["scenarios"].get(scenario_id)
    if scenario is None:
        raise ValueError(f"Scenario '{scenario_id}' not found in {path}")

    controls = [
        check_documents(scenario["documents"]),
        check_prompt(scenario["prompt"]),
        check_monitoring(scenario["monitoring"]),
        check_escalation(scenario["escalation"]),
        check_revalidation(scenario["revalidation"]),
    ]

    critical_fail = any(c["critical"] and not c["pass"] for c in controls)
    all_pass      = all(c["pass"] for c in controls)
    gaps          = [c["finding"] for c in controls if not c["pass"]]

    if critical_fail:
        overall_status = "Fail"
    elif all_pass:
        overall_status = "Pass"
    else:
        overall_status = "Conditional"

    return {
        "scenario":       scenario_id,
        "label":          scenario.get("label", ""),
        "use_case_risk":  scenario.get("use_case_risk", "Unknown"),
        "intended_use":   scenario.get("intended_use", ""),
        "controls":       controls,
        "critical_fail":  critical_fail,
        "overall_status": overall_status,
        "gaps":           gaps,
        "yaml_summary":   scenario.get("governance_summary", {}),
    }


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    for scenario_id in ["T001", "T002", "T003"]:
        result = run_governance_checks(scenario_id)
        print(f"\n{'='*60}")
        print(f"Scenario : {result['scenario']} — {result['label']}")
        print(f"Risk     : {result['use_case_risk']}")
        print(f"Status   : {result['overall_status']}  (critical_fail={result['critical_fail']})")
        print("Controls:")
        for c in result["controls"]:
            status = "PASS" if c["pass"] else ("CRITICAL FAIL" if c["critical"] else "FAIL")
            print(f"  [{status:^13}]  {c['control']}")
        if result["gaps"]:
            print("Gaps:")
            for g in result["gaps"]:
                print(f"  - {g}")
