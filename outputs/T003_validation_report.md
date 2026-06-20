# Validation Report — T003
**Optimized RAG — Current Documents — Full Governance**

| Field | Value |
|-------|-------|
| Scenario ID | T003 |
| Report Date | 2026-06-16 |
| Use Case Risk | High |
| Overall Conclusion | 🟢 Acceptable with Conditions |

---

## 1. Use Case Overview

Scenario T003 - Optimized RAG, Current Documents, Full Governance

## 2. Intended Use

Answer employee questions about model risk management and AI secure development requirements

## 3. Key Risks

- Context precision is marginal — some retrieval noise remains
- Ongoing risk of corpus becoming outdated as regulations evolve
- Continued adherence to governance controls is required
- Annual revalidation required to sustain assurance over time

## 4. Validation Questions

| # | Validation Question | Metric | Score | Rating |
|---|---------------------|--------|-------|--------|
| 1 | Are outputs grounded in authoritative sources? | faithfulness | 0.9075 | ✅ Satisfactory |
| 2 | Are responses relevant to the question asked? | answer_relevancy | 0.9650 | ✅ Satisfactory |
| 3 | Is relevant information consistently retrieved? | context_recall | 0.8875 | ✅ Satisfactory |
| 4 | Is retrieval focused, avoiding noise? | context_precision | 0.6425 | ⚠️  Marginal |

## 5. Evaluation Evidence

**Overall metric status: Marginal**

- Satisfactory: 3 / 4
- Marginal: 1 / 4
- Unsatisfactory: 0 / 4

> Scores generated using Gemini custom scorer via `evaluation/ragas_runner.py`.
> Thresholds: ≥ 0.80 Satisfactory · 0.60–0.79 Marginal · < 0.60 Unsatisfactory

### faithfulness
- **Score:** 0.9075 — ✅ Satisfactory
- **Validation question:** Are outputs grounded in authoritative sources?
- **Rationale:** Faithfulness measures whether the generated answer is supported by the retrieved context. Low scores indicate hallucination or unsupported claims.

### answer_relevancy
- **Score:** 0.9650 — ✅ Satisfactory
- **Validation question:** Are responses relevant to the question asked?
- **Rationale:** Answer relevancy measures whether the generated response addresses the user's question. Low scores indicate off-topic or evasive answers.

### context_recall
- **Score:** 0.8875 — ✅ Satisfactory
- **Validation question:** Is relevant information consistently retrieved?
- **Rationale:** Context recall measures whether the retrieval pipeline surfaces the information needed to answer each question. Low scores indicate retrieval gaps.

### context_precision
- **Score:** 0.6425 — ⚠️  Marginal
- **Validation question:** Is retrieval focused, avoiding noise?
- **Rationale:** Context precision measures whether retrieved chunks are useful rather than noisy. Low scores indicate the retriever is surfacing irrelevant content.

## 6. Governance Evidence

**Overall governance status: Pass**

| Control Area | Status | Finding |
|--------------|--------|---------|
| Source Documents | ✅ Pass | All source documents are approved and current. |
| Prompt Governance | ✅ Pass | Prompt is versioned and change-controlled. Last reviewed: 2026-06-01. |
| Monitoring | ✅ Pass | Monitoring process is defined with output sampling and drift detection. |
| Human Escalation | ✅ Pass | Human escalation path is defined and has been tested. |
| Revalidation | ✅ Pass | Revalidation triggers and schedule are defined. Triggers: Change to foundation model provider, Change to retrieval corpus, Material change to prompt, Regulatory guidance update, Annual scheduled revalidation. |

### Source Document Detail

| Document | Version | Status | Approved |
|----------|---------|--------|----------|
| SR2602.pdf | SR 26-2 (2026) | Current | ✅ Yes |
| Synthetic AI SDL Standard.pdf | AI-SDL v2.0 | Current | ✅ Yes |

## 7. Validation Conclusion

**🟢 Acceptable with Conditions**

**Rule applied:** Rule 4: Satisfactory/Marginal metrics + full governance → Acceptable with Conditions

Metric evidence is satisfactory or marginal across validation questions — no metric fell below the unsatisfactory threshold. Governance controls are in place and verified. The system may be deployed subject to the conditions listed. Ongoing monitoring and adherence to the revalidation schedule are mandatory.

## 8. Required Actions

1. Maintain prompt change control process
2. Continue monthly embedding drift monitoring
3. Conduct annual revalidation per schedule
4. Review source document currency on regulatory update cycle
5. Revalidation is required upon any of the following: Change to foundation model provider; Change to retrieval corpus; Material change to prompt; Regulatory guidance update; Annual scheduled revalidation.

## 9. Monitoring Recommendations

The following monitoring controls are in place and should be maintained:

- Weekly output sampling in place. Embedding drift monitored monthly.
- Alert on faithfulness score drop below 0.70 in production sampling.
- Alert on context precision drop below 0.55.

## 10. Revalidation Triggers

Revalidation is required upon any of the following:

- Change to foundation model provider
- Change to retrieval corpus
- Material change to prompt
- Regulatory guidance update
- Annual scheduled revalidation

---

*Report generated by AI Validation Framework · 2026-06-16*
