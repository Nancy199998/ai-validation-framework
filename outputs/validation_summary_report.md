# AI Validation Framework — Cross-Scenario Summary Report

**"Evaluation generates evidence. Validation transforms evidence into assurance. Governance determines whether assurance can be sustained over time."**

| Field | Value |
|-------|-------|
| Report Date | 2026-06-16 |
| Use Case | RAG-based Q&A — Model Risk Management & AI Secure Development |
| Risk Level | High |
| Scenarios Assessed | T001, T002, T003 |

---

## Overview

This report summarises the validation outcomes across three scenarios that demonstrate a controlled progression in RAG configuration quality and governance maturity. Each scenario uses the same use case, the same test set, and the same validation framework — only the RAG configuration, source documents, and governance controls change.

The purpose is not to find the best-performing system. It is to show that **performance and assurance are not the same thing**, and that the path from one to the other requires governance — not just better metrics.

---

## Scenario Comparison

| | T001 | T002 | T003 |
|-|------|------|------|
| **RAG Configuration** | Config A — Basic | Config B — Optimised + Reranking | Config B — Optimised + Reranking |
| **Source Documents** | Outdated (superseded) | Outdated (superseded) | Current (approved) |
| **Governance Controls** | None | None | Full |
| **Validation Conclusion** | 🔴 Not Acceptable | 🔴 Not Acceptable | 🟢 Acceptable with Conditions |

---

## Metric Scores Across All Scenarios

| Metric | Validation Question | T001 | T002 | T003 |
|--------|-------------------|:----:|:----:|:----:|
| **faithfulness** | Are outputs grounded in authoritative sources? | 0.624 ⚠️ | 0.700 ⚠️ | 0.908 ✅ |
| **answer_relevancy** | Are responses relevant to the question asked? | 0.909 ✅ | 0.874 ✅ | 0.965 ✅ |
| **context_recall** | Is relevant information consistently retrieved? | 0.627 ⚠️ | 0.625 ⚠️ | 0.888 ✅ |
| **context_precision** | Is retrieval focused, avoiding noise? | 0.579 ❌ | 0.558 ❌ | 0.643 ⚠️ |
| **Overall Metric Status** | | Unsatisfactory | Unsatisfactory | Marginal |
| **Governance Status** | | Fail | Fail | Pass |
| **Validation Conclusion** | | 🔴 Not Acceptable | 🔴 Not Acceptable | 🟢 Acceptable with Conditions |

Thresholds: ✅ ≥ 0.80 Satisfactory · ⚠️ 0.60–0.79 Marginal · ❌ < 0.60 Unsatisfactory

---

## The Progression: What Changed and Why It Matters

### T001 → T002: Better RAG, Same Conclusion

Config B introduces cross-encoder reranking on top of the basic vector retrieval used in Config A. The effect on metrics is visible:

- **faithfulness** improves from 0.624 to 0.700 — the reranker is surfacing better-grounded chunks
- **answer_relevancy** remains strong at 0.874 — the system stays on-topic
- **context_recall** is essentially unchanged at 0.625 — the relevant information exists in the corpus but retrieval gaps persist
- **context_precision** marginally worsens from 0.579 to 0.558 — optimised retrieval surfaces more content, including some noise

**Despite these improvements, the conclusion does not change.**

Both T001 and T002 are **Not Acceptable** — not because the metrics are bad, but because the source documents are superseded. The reranker surfaces the best available chunks from an outdated corpus. It does so more effectively in T002 than T001. But "more effectively retrieving superseded guidance" is not a quality improvement for a compliance use case — it is a more efficient path to the wrong answer.

This is the central demonstration of the framework: **you cannot evaluate your way to assurance if the foundation is wrong.**

---

### T002 → T003: Same RAG Config, Different Conclusion

T003 uses the same Config B RAG setup as T002. The only changes are:

1. Source documents replaced with current, approved versions (SR 26-2, AI-SDL v2.0)
2. Full governance controls implemented and verified

The metric improvement is substantial:

- **faithfulness** rises from 0.700 to 0.908 — outputs are now grounded in authoritative, current guidance
- **answer_relevancy** rises from 0.874 to 0.965 — strong throughout
- **context_recall** rises from 0.625 to 0.888 — the current documents contain the information the test questions require
- **context_precision** rises from 0.558 to 0.643 — still marginal, indicating some retrieval noise remains

**The conclusion changes from Not Acceptable to Acceptable with Conditions.**

But note: the metric improvement alone did not change the conclusion. The governance controls changed it. If T003 had current documents but no governance controls, the framework would have returned **Conditional — Review Required**, not Acceptable with Conditions. Both evidence streams are required.

---

## Governance Evidence Summary

| Control Area | T001 | T002 | T003 |
|-------------|:----:|:----:|:----:|
| Source Documents (approved & current) | ❌ Critical Fail | ❌ Critical Fail | ✅ Pass |
| Prompt Governance (versioned & change-controlled) | ❌ Fail | ❌ Fail | ✅ Pass |
| Monitoring (output sampling & drift detection) | ❌ Fail | ❌ Fail | ✅ Pass |
| Human Escalation (defined & tested) | ❌ Fail | ❌ Fail | ✅ Pass |
| Revalidation (triggers & schedule defined) | ❌ Fail | ❌ Fail | ✅ Pass |
| **Overall Governance Status** | **Fail** | **Fail** | **Pass** |

---

## Risk Rules Applied

| Scenario | Rule Applied | Conclusion |
|----------|-------------|------------|
| T001 | Rule 1: Unapproved/superseded source documents → Not Acceptable | 🔴 Not Acceptable |
| T002 | Rule 1: Unapproved/superseded source documents → Not Acceptable | 🔴 Not Acceptable |
| T003 | Rule 4: Satisfactory/Marginal metrics + full governance → Acceptable with Conditions | 🟢 Acceptable with Conditions |

**Rule 1 is unconditional.** No metric score can override it. This reflects real-world validation practice: in regulated industries, using superseded guidance as a knowledge source is a substantive failure regardless of how well the system retrieves from it.

---

## Key Learnings for Readers

### 1. Evaluation is necessary but not sufficient

Evaluation answers the question: *how well does the system perform on a test set?*

Validation answers a different question: *does the evidence support safe deployment?*

These are not the same question. A system can score well on a test set and still be unsuitable for deployment — because the test set was generated from superseded documents, because there is no mechanism to detect when performance degrades in production, or because there is no human escalation path when the system encounters questions it cannot reliably answer.

Evaluation is an input to validation. It is not validation itself.

---

### 2. The source corpus is a governance control, not just a technical input

Most RAG implementations treat document selection as a technical decision: which documents are relevant, how to chunk them, how to embed them. This is correct — but incomplete.

From a validation perspective, **every source document is a governance decision**. Questions that must be answered before deployment include: who approved this document for use? Is it current? What is the process for detecting when it becomes outdated? Who is responsible for replacing it?

T002 shows what happens when these questions are not asked. The reranker performs well. The metrics improve. The system confidently retrieves and summarises superseded regulatory guidance. Without the governance layer, none of this would be visible.

---

### 3. Strong metrics against a bad corpus are a risk, not a reassurance

This is the subtlest point in the framework, and the most important one for practitioners to internalise.

When a RAG system produces high faithfulness scores, it means the generated answers are well-supported by the retrieved context. That is genuinely good — it means the system is not hallucinating. But it says nothing about whether the retrieved context is correct, current, or authoritative.

In T002, faithfulness of 0.700 means the system is faithfully reproducing what SR 11-7 says. SR 11-7 was superseded by SR 26-2. The system is accurately reflecting outdated guidance. High faithfulness in this context is not a quality signal — it is evidence that the system is doing its job well on the wrong source material.

**A metric can only be interpreted in the context of what it is measuring.**

---

### 4. Governance controls are evidence, not bureaucracy

The five governance controls assessed in this framework — source document approval, prompt versioning, monitoring, human escalation, and revalidation triggers — are sometimes perceived as compliance overhead. This framing is wrong.

Each control addresses a specific failure mode:

| Control | Failure mode it prevents |
|---------|------------------------|
| Source document approval | Deployment against unauthorised or outdated knowledge |
| Prompt versioning | Silent drift in system behaviour after changes |
| Monitoring | Undetected performance degradation in production |
| Human escalation | No recovery path when the system fails on high-stakes queries |
| Revalidation triggers | Continued reliance on a validation that no longer reflects the current system |

When all five are in place and verified, the validation framework can conclude that assurance is not just present — it is sustainable. When any are missing, assurance may exist at the point of evaluation but cannot be maintained over time.

---

### 5. "Acceptable with Conditions" is the right outcome for a well-governed system

T003 does not conclude "Approved" or "No issues found." It concludes **Acceptable with Conditions** — and that is intentional.

No AI system operating in a high-risk domain should be unconditionally approved. The conditions attached to T003 are not caveats or hedges. They are the ongoing commitments required to sustain the assurance that validation established:

- Maintain prompt change control
- Continue monitoring per defined schedule
- Conduct annual revalidation
- Review source document currency on the regulatory update cycle

If any of these conditions lapses, the assurance lapses with it. The system does not become unacceptable overnight — but the basis for concluding it is acceptable has eroded, and revalidation is required.

**Assurance is not a one-time certification. It is a sustained state that requires active maintenance.**

---

### 6. The gap between T002 and T003 is a governance gap, not a technology gap

This is worth stating explicitly because it has direct implications for how organisations should invest.

The metric improvements from T002 to T003 are real, and they are driven by the corpus change. Replacing superseded documents with current ones improved faithfulness by 0.208 points and context recall by 0.263 points. These are material gains.

But the conclusion change — from Not Acceptable to Acceptable with Conditions — was not driven by metrics alone. It required governance controls to be in place. An organisation that invests only in RAG optimisation (better rerankers, better embeddings, better chunking) without investing in governance will move from T001 to T002: better performance, same conclusion.

The path from T002 to T003 requires a different kind of investment.

---

## Summary

| | T001 | T002 | T003 |
|-|:----:|:----:|:----:|
| RAG quality | Basic | Optimised | Optimised |
| Metric quality | Unsatisfactory | Unsatisfactory | Marginal |
| Governance | None | None | Full |
| Conclusion | 🔴 Not Acceptable | 🔴 Not Acceptable | 🟢 Acceptable with Conditions |
| **What this shows** | Baseline failure | **Metrics ≠ assurance** | Assurance requires both |

The framework does not argue that metrics are unimportant. Metrics are essential — they are the primary evidence that a system performs as intended. The framework argues that metrics are insufficient on their own, and that the gap between evaluation and assurance is closed by governance.

Evaluation tells you what the system does. Validation tells you whether what it does is safe enough to deploy. Governance tells you whether that answer will still be true next month.

---

*Report generated by AI Validation Framework · 2026-06-16*  
*Companion to: "Beyond Evaluation: Building Assurance for GenAI and Agentic AI Systems"*
