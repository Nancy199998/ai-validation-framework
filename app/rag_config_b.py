import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.cross_encoders import HuggingFaceCrossEncoder

load_dotenv()

# Paths
CHROMA_CURRENT_PATH = "data/chroma_current"
CHROMA_OUTDATED_PATH = "data/chroma_outdated"

def format_docs(docs):
    return "\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )

def build_rag_chain(vectorstore_path, use_outdated=False):
    """
    Config B - Optimized RAG
    - Larger initial retrieval pool (k=6)
    - Cross-encoder reranking
    - Grounded prompt with source citation instruction
    - Returns top 3 after reranking
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    vectorstore = Chroma(
        persist_directory=vectorstore_path,
        embedding_function=embeddings
    )

    # Retrieve more candidates then rerank
    base_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}
    )

    cross_encoder = HuggingFaceCrossEncoder(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
    )

    class RerankedRetriever:
        def __init__(self, retriever, reranker, top_n=3):
            self.retriever = retriever
            self.reranker = reranker
            self.top_n = top_n

        def invoke(self, query):
            docs = self.retriever.invoke(query)
            pairs = [[query, doc.page_content] for doc in docs]
            scores = self.reranker.score(pairs)
            ranked = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
            return [doc for _, doc in ranked[:self.top_n]]

    retriever = RerankedRetriever(base_retriever, cross_encoder, top_n=3)


    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

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

    config_label = "Config B - Optimized RAG (OUTDATED docs)" if use_outdated else "Config B - Optimized RAG (CURRENT docs)"
    return chain, retriever, config_label


def run_query(chain, retriever, question):
    """Run a single query and return answer and sources."""
    answer = chain.invoke(question)
    docs = retriever.invoke(question)
    sources = list(set([
        doc.metadata.get("source", "unknown")
        for doc in docs
    ]))
    return answer, sources


if __name__ == "__main__":
    print("=== Testing Config B - Optimized RAG ===\n")

    chain, retriever, label = build_rag_chain(CHROMA_CURRENT_PATH, use_outdated=False)
    print(f"Configuration: {label}\n")

    test_questions = [
        "What is the purpose of model validation?",
        "What are the key components of an AI secure development lifecycle?",
        "What are the main risks associated with AI models?"
    ]

    for question in test_questions:
        print(f"Q: {question}")
        answer, sources = run_query(chain, retriever, question)
        print(f"A: {answer}")
        print(f"Sources: {sources}")
        print("-" * 60)