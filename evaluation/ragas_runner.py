"""
evaluation/ragas_runner.py

Runs RAGAS metrics against Config A and Config B for a given document set.
Saves per-question results and summary scores to CSV files in outputs/.

Usage:
    python -u evaluation/ragas_runner.py --scenario T001
    python -u evaluation/ragas_runner.py --scenario T002
    python -u evaluation/ragas_runner.py --scenario T003

Outputs:
    outputs/T001_raw_results.csv   -- per-question scores
    outputs/T001_summary.csv       -- mean scores per metric
"""

import os
import sys
import argparse
import time
import pandas as pd
import yaml
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from datasets import Dataset

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CHROMA_CURRENT_PATH  = "data/chroma_current"
CHROMA_OUTDATED_PATH = "data/chroma_outdated"
TEST_SET_PATH        = "data/test_set.csv"
GOVERNANCE_PATH      = "data/governance_inputs.yaml"
OUTPUTS_DIR          = "outputs"

os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )


def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )


def format_docs(docs):
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


# ---------------------------------------------------------------------------
# Config A — basic retriever
# ---------------------------------------------------------------------------

def build_config_a(vectorstore_path):
    embeddings  = get_embeddings()
    vectorstore = Chroma(persist_directory=vectorstore_path, embedding_function=embeddings)
    retriever   = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    llm         = get_llm()

    prompt = PromptTemplate.from_template("""
You are a compliance assistant. Answer the question using ONLY the context below.
If the answer is not in the context, say "This information is not available in the approved documents."

Context:
{context}

Question: {question}

Answer:
""")

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


# ---------------------------------------------------------------------------
# Config B — reranked retriever
# ---------------------------------------------------------------------------

class RerankedRetriever:
    def __init__(self, retriever, reranker, top_n=3):
        self.retriever = retriever
        self.reranker  = reranker
        self.top_n     = top_n

    def invoke(self, query):
        docs  = self.retriever.invoke(query)
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self.reranker.score(pairs)
        ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[:self.top_n]]


def build_config_b(vectorstore_path):
    embeddings    = get_embeddings()
    vectorstore   = Chroma(persist_directory=vectorstore_path, embedding_function=embeddings)
    base_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 6})
    cross_encoder  = HuggingFaceCrossEncoder(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    retriever      = RerankedRetriever(base_retriever, cross_encoder, top_n=3)
    llm            = get_llm()

    prompt = PromptTemplate.from_template("""
You are a compliance assistant. Answer the question using ONLY the context below.
Always cite the source document for each point you make.
If the answer is not in the context, say "This information is not available in the approved documents."

Context:
{context}

Question: {question}

Answer (with source citations):
""")

    chain = (
        {"context": lambda q: format_docs(retriever.invoke(q)), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever


# ---------------------------------------------------------------------------
# Run queries and collect RAGAS inputs
# ---------------------------------------------------------------------------

def collect_ragas_inputs(chain, retriever, test_df, delay=4, scenario_id="T001"):
    records = []
    checkpoint_path = os.path.join(OUTPUTS_DIR, f"checkpoint_{scenario_id}.json")

    # Load existing checkpoint if present
    completed_ids = set()
    if os.path.exists(checkpoint_path):
        import json
        with open(checkpoint_path) as f:
            records = json.load(f)
        completed_ids = {r["question_id"] for r in records}
        print(f"  Resuming from checkpoint — {len(records)} questions already done.\n")

    for i, row in test_df.iterrows():
        if row["Question_ID"] in completed_ids:
            continue

        question     = row["Question"]
        ground_truth = row.get("Expected_Answer", row.get("answer", ""))

        print(f"  [{i+1}/{len(test_df)}] {question[:70]}...")
        try:
            answer = chain.invoke(question)
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(question)
            else:
                docs = retriever.get_relevant_documents(question)
            contexts = [doc.page_content for doc in docs]
        except Exception as e:
            print(f"         ⚠️  Error: {e} — skipping.")
            answer   = "Error generating answer."
            contexts = []

        records.append({
            "question":     question,
            "answer":       answer,
            "contexts":     contexts,
            "ground_truth": ground_truth,
            "question_id":  row["Question_ID"],
            "category":     row["Category"],
            "risk_level":   row["Risk_Level"],
        })

        # Save checkpoint after every question
        import json
        with open(checkpoint_path, "w") as f:
            json.dump(records, f)

        time.sleep(delay)

    return records


# ---------------------------------------------------------------------------
# Run RAGAS evaluation
# ---------------------------------------------------------------------------

def run_ragas(records, scenario_id="T001"):
    """Score records using Gemini directly — bypasses ragas executor entirely."""
    import json

    llm = get_llm()

    def score_faithfulness(question, answer, contexts):
        context_str = "\n\n".join(contexts)
        prompt = f"""Rate how faithful this answer is to the provided context.
Score 0.0 to 1.0 where 1.0 means every claim in the answer is supported by the context.

Context:
{context_str}

Answer:
{answer}

Respond with ONLY a JSON object like: {{"score": 0.85}}"""
        try:
            result = llm.invoke(prompt).content
            return json.loads(result.strip().strip("```json").strip("```"))["score"]
        except:
            return float("nan")

    def score_answer_relevancy(question, answer):
        prompt = f"""Rate how relevant this answer is to the question.
Score 0.0 to 1.0 where 1.0 means the answer directly and completely addresses the question.

Question: {question}
Answer: {answer}

Respond with ONLY a JSON object like: {{"score": 0.85}}"""
        try:
            result = llm.invoke(prompt).content
            return json.loads(result.strip().strip("```json").strip("```"))["score"]
        except:
            return float("nan")

    def score_context_recall(question, answer, ground_truth, contexts):
        context_str = "\n\n".join(contexts)
        prompt = f"""Rate how well the retrieved context covers the ground truth answer.
Score 0.0 to 1.0 where 1.0 means all information in the ground truth is present in the context.

Ground Truth: {ground_truth}
Context: {context_str}

Respond with ONLY a JSON object like: {{"score": 0.85}}"""
        try:
            result = llm.invoke(prompt).content
            return json.loads(result.strip().strip("```json").strip("```"))["score"]
        except:
            return float("nan")

    def score_context_precision(question, contexts, ground_truth):
        context_str = "\n\n".join(contexts)
        prompt = f"""Rate how precise and relevant the retrieved context is for answering the question.
Score 0.0 to 1.0 where 1.0 means all retrieved context is relevant with no noise.

Question: {question}
Ground Truth: {ground_truth}
Context: {context_str}

Respond with ONLY a JSON object like: {{"score": 0.85}}"""
        try:
            result = llm.invoke(prompt).content
            return json.loads(result.strip().strip("```json").strip("```"))["score"]
        except:
            return float("nan")

    all_scores = []
    for i, r in enumerate(records):
        print(f"  Scoring [{i+1}/{len(records)}]...")
        scores = {
            "faithfulness":      score_faithfulness(r["question"], r["answer"], r["contexts"]),
            "answer_relevancy":  score_answer_relevancy(r["question"], r["answer"]),
            "context_recall":    score_context_recall(r["question"], r["answer"], r["ground_truth"], r["contexts"]),
            "context_precision": score_context_precision(r["question"], r["contexts"], r["ground_truth"]),
        }
        all_scores.append(scores)
        time.sleep(2)

    scores_df = pd.DataFrame(all_scores)
    meta_df = pd.DataFrame([{
        "question_id": r["question_id"],
        "category":    r["category"],
        "risk_level":  r["risk_level"],
        "answer":      r["answer"],
    } for r in records])

    return pd.concat([meta_df.reset_index(drop=True), scores_df.reset_index(drop=True)], axis=1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(scenario):
    print(f"\n{'='*60}")
    print(f" RAGAS Evaluation Runner — Scenario {scenario}")
    print(f"{'='*60}\n")

    # Load governance config
    with open(GOVERNANCE_PATH) as f:
        governance = yaml.safe_load(f)

    if scenario not in governance["scenarios"]:
        print(f"ERROR: Scenario '{scenario}' not found in governance_inputs.yaml")
        sys.exit(1)

    config = governance["scenarios"][scenario]
    rag_config   = config["rag_config"]       # "A" or "B"
    doc_set      = config["document_set"]     # "current" or "outdated"

    vectorstore_path = CHROMA_CURRENT_PATH if doc_set == "current" else CHROMA_OUTDATED_PATH

    print(f"RAG Config:    {rag_config}")
    print(f"Document set:  {doc_set}  →  {vectorstore_path}")
    print(f"Label:         {config['label']}\n")

    # Load test set
    test_df = pd.read_csv(TEST_SET_PATH)
    print(f"Test set loaded: {len(test_df)} questions\n")

    # Build chain
    print("Building RAG chain...")
    if rag_config == "A":
        chain, retriever = build_config_a(vectorstore_path)
    else:
        chain, retriever = build_config_b(vectorstore_path)
    print("Chain ready.\n")

    # Collect inputs
    print("Running queries (with rate-limit delay between calls)...")
    records = collect_ragas_inputs(chain, retriever, test_df, delay=4, scenario_id=scenario)
    print(f"\nAll {len(records)} queries complete.\n")

    # Run RAGAS
    print("Running RAGAS metrics...")
    results_df = run_ragas(records, scenario_id=scenario)
    print("RAGAS evaluation complete.\n")

    # Save raw results
    raw_path = os.path.join(OUTPUTS_DIR, f"{scenario}_raw_results.csv")
    results_df.to_csv(raw_path, index=False)
    print(f"Raw results saved to: {raw_path}")

    # Save summary
    metric_cols = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
    available   = [c for c in metric_cols if c in results_df.columns]
    summary     = results_df[available].mean().reset_index()
    summary.columns = ["metric", "mean_score"]
    summary["scenario"]   = scenario
    summary["rag_config"] = rag_config
    summary["doc_set"]    = doc_set

    summary_path = os.path.join(OUTPUTS_DIR, f"{scenario}_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Summary saved to:     {summary_path}")

    # Print summary to console
    print(f"\n--- {scenario} Score Summary ---")
    for _, row in summary.iterrows():
        print(f"  {row['metric']:<25} {row['mean_score']:.4f}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation for a scenario")
    parser.add_argument("--scenario", required=True, choices=["T001", "T002", "T003"],
                        help="Scenario ID to evaluate (T001, T002, or T003)")
    args = parser.parse_args()
    main(args.scenario)
