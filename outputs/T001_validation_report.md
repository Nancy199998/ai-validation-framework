# Validation Report — T001
**Basic RAG — Outdated Documents — No Governance**

| Field | Value |
|-------|-------|
| Scenario ID | T001 |
| Report Date | 2026-06-16 |
| Use Case Risk | High |
| Overall Conclusion | 🔴 Not Acceptable |

---

## 1. Use Case Overview

Scenario T001 - Basic RAG, Outdated Documents, No Governance

## 2. Intended Use

Answer employee questions about model risk management and AI secure development requirements

## 3. Key Risks

- Responses grounded in superseded regulatory guidance
- No mechanism to detect when source documents become outdated
- No human escalation path for uncertain or high-stakes queries
- No prompt change control — silent drift possible

## 4. Validation Questions

| # | Validation Question | Metric | Score | Rating |
|---|---------------------|--------|-------|--------|
| 1 | Are outputs grounded in authoritative sources? | faithfulness | 0.6237 | ⚠️  Marginal |
| 2 | Are responses relevant to the question asked? | answer_relevancy | 0.9090 | ✅ Satisfactory |
| 3 | Is relevant information consistently retrieved? | context_recall | 0.6265 | ⚠️  Marginal |
| 4 | Is retrieval focused, avoiding noise? | context_precision | 0.5789 | ❌ Unsatisfactory |

## 5. Evaluation Evidence

**Overall metric status: Unsatisfactory**

- Satisfactory: 1 / 4
- Marginal: 2 / 4
- Unsatisfactory: 1 / 4

> Scores generated using Gemini custom scorer via `evaluation/ragas_runner.py`.
> Thresholds: ≥ 0.80 Satisfactory · 0.60–0.79 Marginal · < 0.60 Unsatisfactory

### faithfulness
- **Score:** 0.6237 — ⚠️  Marginal
- **Validation question:** Are outputs grounded in authoritative sources?
- **Rationale:** Faithfulness measures whether the generated answer is supported by the retrieved context. Low scores indicate hallucination or unsupported claims.

### answer_relevancy
- **Score:** 0.9090 — ✅ Satisfactory
- **Validation question:** Are responses relevant to the question asked?
- **Rationale:** Answer relevancy measures whether the generated response addresses the user's question. Low scores indicate off-topic or evasive answers.

### context_recall
- **Score:** 0.6265 — ⚠️  Marginal
- **Validation question:** Is relevant information consistently retrieved?
- **Rationale:** Context recall measures whether the retrieval pipeline surfaces the information needed to answer each question. Low scores indicate retrieval gaps.

### context_precision
- **Score:** 0.5789 — ❌ Unsatisfactory
- **Validation question:** Is retrieval focused, avoiding noise?
- **Rationale:** Context precision measures whether retrieved chunks are useful rather than noisy. Low scores indicate the retriever is surfacing irrelevant content.

## 6. Governance Evidence

**Overall governance status: Fail**

| Control Area | Status | Finding |
|--------------|--------|---------|
| Source Documents | ❌ Critical Fail | One or more source documents are superseded or not approved for use. This is a critical governance failure — metrics cannot compensate. |
| Prompt Governance | ❌ Fail | Prompt is not versioned or change-controlled. Changes cannot be tracked or rolled back. |
| Monitoring | ❌ Fail | No monitoring process defined. Performance degradation will go undetected. |
| Human Escalation | ❌ Fail | Human escalation path is not defined or has not been tested. |
| Revalidation | ❌ Fail | No revalidation triggers or schedule defined. There is no mechanism to detect when revalidation is required. |

### Source Document Detail

| Document | Version | Status | Approved |
|----------|---------|--------|----------|
| sr1107a1.pdf | SR 11-7 (2011) | Superseded (superseded by SR 26-2) | ❌ No |
| synthetic AI_SDL_v1_0_SUPERSEDED.pdf | AI-SDL v1.0 | Superseded (superseded by AI-SDL v2.0) | ❌ No |

### Governance Gaps Identified

- One or more source documents are superseded or not approved for use. This is a critical governance failure — metrics cannot compensate.
- Prompt is not versioned or change-controlled. Changes cannot be tracked or rolled back.
- No monitoring process defined. Performance degradation will go undetected.
- Human escalation path is not defined or has not been tested.
- No revalidation triggers or schedule defined. There is no mechanism to detect when revalidation is required.

## 7. Validation Conclusion

**🔴 Not Acceptable**

**Rule applied:** Rule 1: Unapproved/superseded source documents → Not Acceptable

One or more source documents are superseded or unapproved. Metric scores — however strong — cannot provide assurance when the knowledge corpus is not authoritative. Evaluation evidence generated against an unapproved corpus does not constitute valid validation. The system must not be deployed or continued in production.

## 8. Required Actions

1. Replace all source documents with approved, current versions.
2. Rebuild vector store from approved corpus.
3. Re-run full evaluation suite after corpus replacement.
4. Submit for re-validation before any deployment or continued use.

## 9. Monitoring Recommendations

No monitoring controls are currently in place. The following are required:

- Define and implement an output sampling process (minimum weekly).
- Implement embedding drift detection (minimum monthly).
- Establish alerting thresholds for faithfulness and context precision.
- Assign ownership for monitoring review and escalation.

## 10. Revalidation Triggers

No revalidation triggers are currently defined. The following are recommended:

- Change to foundation model provider or version
- Change to retrieval corpus or source documents
- Material change to prompt
- Regulatory guidance update affecting the use case
- Annual scheduled revalidation

---

*Report generated by AI Validation Framework · 2026-06-16*
