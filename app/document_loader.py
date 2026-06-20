import time
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# Paths
CURRENT_DOCS_PATH = "data/documents/current"
OUTDATED_DOCS_PATH = "data/documents/outdated"
CHROMA_CURRENT_PATH = "data/chroma_current"
CHROMA_OUTDATED_PATH = "data/chroma_outdated"

def load_pdfs_from_folder(folder_path):
    """Load all PDFs from a folder."""
    documents = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            filepath = os.path.join(folder_path, filename)
            print(f"Loading: {filename}")
            loader = PyPDFLoader(filepath)
            documents.extend(loader.load())
    print(f"Total pages loaded: {len(documents)}")
    return documents

def split_documents(documents, chunk_size=500, chunk_overlap=50):
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")
    return chunks

def build_vectorstore(chunks, persist_path):
    """Build and persist ChromaDB vectorstore."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    # Process in smaller batches with delay to avoid rate limits
    batch_size = 50
    all_chunks = chunks
    
    vectorstore = None
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        print(f"Embedding batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}...")
        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_path
            )
        else:
            vectorstore.add_documents(batch)
        if i + batch_size < len(all_chunks):
            print("Waiting 60s for rate limit...")
            time.sleep(60)
    
    print(f"Vectorstore saved to: {persist_path}")
    return vectorstore

def load_vectorstore(persist_path):
    """Load existing ChromaDB vectorstore."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    vectorstore = Chroma(
        persist_directory=persist_path,
        embedding_function=embeddings
    )
    return vectorstore


if __name__ == "__main__":
    # print("=== Loading CURRENT documents ===")
    # current_docs = load_pdfs_from_folder(CURRENT_DOCS_PATH)
    # current_chunks = split_documents(current_docs)
    # build_vectorstore(current_chunks, CHROMA_CURRENT_PATH)

    print("\n=== Loading OUTDATED documents ===")
    outdated_docs = load_pdfs_from_folder(OUTDATED_DOCS_PATH)
    outdated_chunks = split_documents(outdated_docs)
    build_vectorstore(outdated_chunks, CHROMA_OUTDATED_PATH)

    print("\nDocument loading complete.")
