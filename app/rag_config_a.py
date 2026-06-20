import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# Paths
CHROMA_CURRENT_PATH = "data/chroma_current"
CHROMA_OUTDATED_PATH = "data/chroma_outdated"

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def build_rag_chain(vectorstore_path, use_outdated=False):
    """
    Config A - Basic RAG
    - Simple similarity search
    - No reranking
    - Basic prompt
    - Fixed chunk retrieval (top 3)
    """
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    vectorstore = Chroma(
        persist_directory=vectorstore_path,
        embedding_function=embeddings
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    prompt = PromptTemplate.from_template("""
    Answer the question based on the context below.
    If you don't know the answer, say "I don't know".

    Context: {context}

    Question: {question}

    Answer:
    """)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    config_label = "Config A - Basic RAG (OUTDATED docs)" if use_outdated else "Config A - Basic RAG (CURRENT docs)"
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
    print("=== Testing Config A - Basic RAG ===\n")

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