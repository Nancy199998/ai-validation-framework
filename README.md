# AI Validation Framework

> **"Evaluation generates evidence. Validation transforms evidence into assurance. Governance determines whether assurance can be sustained over time."**

This project demonstrates the difference between **AI evaluation** and **AI validation** using a RAG (Retrieval-Augmented Generation) system built for a realistic enterprise use case: answering employee questions about model risk management and AI secure development requirements.

Strong metric scores are not enough. This framework shows why — and what governance controls are required to turn evaluation evidence into genuine assurance.

---

## The Core Argument

Most teams stop at evaluation. They run metrics, see good scores, and declare the system ready.

This project shows that approach is insufficient.

| Concept | What it does | What it produces |
|---------|-------------|-----------------|
| **Evaluation** | Measures system performance on a test set | Evidence (scores) |
| **Validation** | Asks whether evidence supports safe deployment | Assurance (or not) |
| **Governance** | Ensures assurance can be sustained over time | Continuity of assurance |

**Scenario T002 is the centrepiece.** Config B (optimised RAG with reranking) produces materially better metric scores than Config A. Yet the validation framework concludes **Not Acceptable** — because the source documents are superseded. High scores against an unapproved corpus are not assurance. They are a measurement of how well the system retrieves and summarises outdated information.

---

## Use Case

**System:** RAG-based Q&A assistant
**Domain:** Financial services regulatory compliance
**Intended use:** Answer employee questions about model risk management (SR 26-2) and AI secure development lifecycle requirements (AI-SDL v2.0)
**Risk level:** High — incorrect answers could lead to non-compliant practices

---

## Three Scenarios

| Scenario | RAG Config | Documents | Governance | Conclusion |
|----------|-----------|-----------|------------|------------|
| **T001** | Config A — Basic RAG | Outdated (superseded) | None | 🔴 Not Acceptable |
| **T002** | Config B — Optimised RAG + Reranking | Outdated (superseded) | None | 🔴 Not Acceptable |
| **T003** | Config B — Optimised RAG + Reranking | Current (approved) | Full | 🟢 Acceptable with Conditions |

The progression is intentional:
- **T001 → T002:** Better RAG configuration, better scores — but same conclusion. Metrics improved; governance did not.
- **T002 → T003:** Same RAG configuration, different documents and governance controls — different conclusion. Governance changed; assurance followed.

---

## Metric Scores

| Metric | Validation Question | T001 | T002 | T003 |
|--------|--------------------:|------|------|------|
| faithfulness | Are outputs grounded in authoritative sources? | 0.624 ⚠️ | 0.700 ⚠️ | 0.908 ✅ |
| answer_relevancy | Are responses relevant to the question asked? | 0.909 ✅ | 0.874 ✅ | 0.965 ✅ |
| context_recall | Is relevant information consistently retrieved? | 0.627 ⚠️ | 0.625 ⚠️ | 0.888 ✅ |
| context_precision | Is retrieval focused, avoiding noise? | 0.579 ❌ | 0.558 ❌ | 0.643 ⚠️ |

Thresholds: ✅ ≥ 0.80 Satisfactory · ⚠️ 0.60–0.79 Marginal · ❌ < 0.60 Unsatisfactory

Notice that T002's metrics are higher than T001's across most measures — yet both scenarios reach the same "Not Acceptable" conclusion. This is the point of the framework: metric improvement alone does not change a validation outcome.

---

## Project Structure

```
validation-framework/
├── app/
│   ├── document_loader.py       # Loads and chunks documents into ChromaDB
│   ├── rag_config_a.py          # Config A: basic RAG (no reranking)
│   └── rag_config_b.py          # Config B: optimised RAG with reranking
├── data/
│   ├── documents/
│   │   ├── current/             # SR 26-2, AI-SDL v2.0 (approved)
│   │   └── outdated/            # SR 11-7, AI-SDL v1.0 (superseded)
│   ├── chroma_current/          # Vector store — current documents
│   ├── chroma_outdated/         # Vector store — outdated documents
│   ├── test_set.csv             # 20 evaluation questions with ground truth
│   └── governance_inputs.yaml   # Governance controls metadata per scenario
├── evaluation/
│   ├── ragas_runner.py          # Option 1: Gemini custom scorer (Python 3.14)
│   └── ragas_runner_v2.py       # Option 2: Real ragas library (Python 3.11)
├── src/
│   ├── evidence_mapper.py       # Maps metric scores to validation questions
│   ├── governance_checker.py    # Assesses governance controls per scenario
│   ├── risk_rules.py            # Derives validation conclusion from evidence
│   └── report_generator.py      # Produces markdown validation reports
├── outputs/
│   ├── checkpoint_T00X.json     # Shared inference checkpoints (both options)
│   ├── T00X_summary.csv         # Option 1 metric scores
│   ├── T00X_raw_results.csv     # Option 1 per-question results
│   ├── T00X_validation_report.md # Per-scenario validation reports
│   └── validation_summary_report.md # Cross-scenario summary (working copy)
└── docs/
    └── validation_summary_report.md # Cross-scenario summary (canonical copy — start here)
```

> **Note on the summary report:** `validation_summary_report.md` is kept in both `docs/` (the canonical, citable copy) and `outputs/` (alongside the other per-run artefacts, for convenience when reviewing a single evaluation pass). The content is identical; `docs/` is the one to link to.

---

## How to Run

### Prerequisites

- Python 3.11 (for ragas) and/or Python 3.14 (for custom scorer)
- Google Gemini API key (paid tier recommended)
- Dependencies installed in respective virtual environments

### Environment Setup

```powershell
# Always set API key manually in each new terminal
$env:GOOGLE_API_KEY = "your_key_here"
```

> **Note:** The `.env` file is unreliable in this environment. Always set the key explicitly.

### Step 0 — Build Vector Stores (first run only)

The evaluation steps below assume `data/chroma_current/` and `data/chroma_outdated/` already exist. They're built by `app/document_loader.py`, which loads the PDFs in `data/documents/current/` and `data/documents/outdated/`, chunks them, and embeds them into ChromaDB.

By default, the script only builds the **outdated** vectorstore — the current-docs block is commented out in `if __name__ == "__main__"` to keep manual runs controlled and avoid unnecessary embedding calls. To build both:

```powershell
venv\Scripts\activate

# Run once as-is (builds OUTDATED vectorstore)
python -u app/document_loader.py

# Then open app/document_loader.py, comment out the OUTDATED block and
# uncomment the CURRENT block in __main__, and run again (builds CURRENT vectorstore)
python -u app/document_loader.py
```

> Embedding runs in batches of 50 chunks with a 60-second pause between batches to respect API rate limits — this is expected and not a hang. A full run can take several minutes depending on document size.

Skip this step if `data/chroma_current/` and `data/chroma_outdated/` already exist with content.

### Step 1 — Run Evaluation (Option 1: Gemini custom scorer)

```powershell
venv\Scripts\activate
python -u evaluation/ragas_runner.py --scenario T001
python -u evaluation/ragas_runner.py --scenario T002
python -u evaluation/ragas_runner.py --scenario T003
```

### Step 2 — Run Evaluation (Option 2: Real ragas library)

```powershell
venv311\Scripts\activate
python -u evaluation/ragas_runner_v2.py --scenario T001
python -u evaluation/ragas_runner_v2.py --scenario T002
python -u evaluation/ragas_runner_v2.py --scenario T003
```

> Checkpoints are shared between both options. Whichever runs first performs inference and saves the checkpoint. The second option reuses it and scores only — no wasted API calls.

### Step 3 — Run Validation Pipeline

```powershell
venv\Scripts\activate
python src/report_generator.py
```

This produces three validation reports in `outputs/`:
- `T001_validation_report.md` — 🔴 Not Acceptable
- `T002_validation_report.md` — 🔴 Not Acceptable
- `T003_validation_report.md` — 🟢 Acceptable with Conditions

---

## Two Evaluation Paths

The `ragas` library is incompatible with Python 3.14 due to asyncio changes. Rather than abandon ragas, this project implements two parallel evaluation paths that share inference checkpoints.

| | Option 1 | Option 2 |
|-|----------|----------|
| Script | `ragas_runner.py` | `ragas_runner_v2.py` |
| Scorer | Gemini LLM via structured prompts | Real ragas `evaluate()` |
| Python | 3.14 (venv) | 3.11 (venv311) |
| Output files | `T00X_summary.csv` | `T00X_summary_ragas.csv` |

---

## Validation Reports

Start with the cross-scenario summary, then read individual reports for detail:

- [Cross-Scenario Summary](docs/validation_summary_report.md) ← start here
- [Last Successful Run](outputs/last_run.md) — confirms the pipeline executes end-to-end
- [T001 Validation Report](outputs/T001_validation_report.md)
- [T002 Validation Report](outputs/T002_validation_report.md) ← the centrepiece scenario
- [T003 Validation Report](outputs/T003_validation_report.md)

---

## Companion Blog Post

This project accompanies the blog post:

**"Beyond Evaluation: Building Assurance for GenAI and Agentic AI Systems"**

The blog post develops the argument that the AI industry's focus on evaluation metrics — while necessary — is insufficient for high-risk deployments. Validation requires combining metric evidence with governance evidence under a structured risk-based framework.

---

## Key Design Decisions

**Governance as a first-class input.** The `governance_inputs.yaml` file treats governance controls as structured, assessable evidence — not narrative commentary. Each control has a pass/fail determination that feeds directly into the risk rules engine.

**What "optimised" means in Config B.** Config A (`app/rag_config_a.py`) retrieves the top 3 chunks by similarity search and answers with a basic prompt. Config B (`app/rag_config_b.py`) retrieves a wider candidate pool (top 6), reranks them with a cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) down to the best 3, and uses a stricter, citation-required prompt. The reranking is real, not simulated — it's the mechanism behind T002's improved metric scores relative to T001.

**Shared checkpoints.** Both evaluation options share checkpoint files so inference is never duplicated regardless of which scorer runs first.

**Rule 1 is unconditional.** No metric score, however high, can override an unapproved source document. This is a deliberate design choice that reflects real-world validation practice in regulated industries.

**No unconditional pass.** Even T003 concludes "Acceptable with Conditions" — not "Approved." Ongoing monitoring and revalidation are always required.

---

## Future Extensions

The next planned extension is **AI Change Materiality** — testing how the framework should respond when previously collected validation evidence stops being sufficient due to a downstream change (model, corpus, or pipeline). Not implemented in this version.

---

*Built to accompany "Beyond Evaluation: Building Assurance for GenAI and Agentic AI Systems"*
