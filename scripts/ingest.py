import os
import sys
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the root project directory (parent of scripts/)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Construct absolute paths for directories in the root project folder
DOCS_PATH = os.path.join(root_dir, "documents")
DB_PATH = os.path.join(root_dir, "vector_store")

def create_vector_store():
    """
    Loads documents, splits them into chunks, creates embeddings,
    and saves them to a FAISS vector store.
    """
    print("Starting document ingestion process...")

    # 1. Load documents from the specified directory
    loader = DirectoryLoader(DOCS_PATH, glob="**/*.md")
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")

    # 2. Split documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f"Split documents into {len(texts)} chunks.")

    # 3. Create embeddings for the text chunks
    # This uses a popular, open-source embedding model.
    # The first time you run this, it will download the model (a few hundred MB).
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    print("Embedding model loaded.")

    # 4. Create a FAISS vector store from the chunks and embeddings
    print("Creating and saving vector store...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_PATH)
    print(f"Vector store created and saved at: {DB_PATH}")

if __name__ == "__main__":
    create_vector_store()