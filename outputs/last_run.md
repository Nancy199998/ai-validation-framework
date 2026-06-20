# Last Successful Run

This file is a point-in-time record of the most recent confirmed end-to-end run of the validation pipeline. It exists as evidence that the framework executes correctly and produces the conclusions described in this repository — consistent with this project's own argument that claims should be backed by evidence, not just stated.

This is **not** a live log. It is updated manually after a confirmed successful run.

---

## Run Record

| Field | Value |
|---|---|
| **Date** | 2026-06-16 |
| **Evaluation path used** | Option 1 — Gemini custom scorer (`ragas_runner.py`) |
| **Python environment** | 3.14 (`venv`) |
| **LLM** | Google Gemini (`gemini-2.5-flash`) |
| **Embedding model** | `models/gemini-embedding-001` |

## Scenarios Run

| Scenario | Pipeline Stage | Result |
|---|---|---|
| T001 | `evidence_mapper.py` → `governance_checker.py` → `risk_rules.py` → `report_generator.py` | ✅ Ran successfully — Conclusion: 🔴 Not Acceptable |
| T002 | same | ✅ Ran successfully — Conclusion: 🔴 Not Acceptable |
| T003 | same | ✅ Ran successfully — Conclusion: 🟢 Acceptable with Conditions |

All three conclusions match the validation reports in `outputs/` and the summary in `docs/validation_summary_report.md`.

## Known Limitation at Time of Run

Option 2 (real `ragas` library, Python 3.11 / `venv311`) was not producing valid scores for T002/T003 as of this run — see `evaluation/ragas_runner_v2.py` and the architecture note in that file. Option 1 is the verified, working path referenced throughout this README.

## A Note on Reproducibility

This is a demonstration framework illustrating an argument (evaluation ≠ validation), not a production system under continuous integration. Dependencies — `ragas`, `langchain`, the Gemini API — will continue to evolve after this date. If you run the pipeline and get different results than recorded here, check dependency versions first; the validation *logic* in `src/risk_rules.py` is the stable, citable part of this project, independent of which scoring backend produced the input metrics.

---

*Update this file after any future confirmed end-to-end run.*
