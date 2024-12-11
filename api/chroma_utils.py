from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
from chromadb.config import Settings
import os
import gc

# Determine the base directory for Chroma
CHROMA_BASE_DIR = "/data/chroma_db" if os.access("/data", os.W_OK) else "./chroma_db"
print(f"Using Chroma directory: {CHROMA_BASE_DIR}")

CHROMA_SETTINGS = Settings(
    anonymized_telemetry=False,
    allow_reset=True,
    is_persistent=True,
    persist_directory=CHROMA_BASE_DIR,
)

# Adjust text splitting parameters as needed
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,     # Reduced from 1000
    chunk_overlap=50,   # Reduced from 200
    length_function=len
)

embedding_function = OpenAIEmbeddings()

# Make sure persist_directory matches CHROMA_BASE_DIR
vectorstore = Chroma(
    persist_directory=CHROMA_BASE_DIR,
    embedding_function=embedding_function,
    client_settings=CHROMA_SETTINGS
)

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    if not documents:
        print(f"No documents loaded from {file_path}.")
    else:
        print(f"Loaded {len(documents)} documents from {file_path}.")

    splits = text_splitter.split_documents(documents)
    print(f"Created {len(splits)} text chunks from {file_path}.")

    # Debug: Print first few chunks
    for i, s in enumerate(splits[:3]):
        print(f"Chunk {i+1}: {s.page_content[:200]}...")

    return splits

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)

        # Add metadata and index in batches
        BATCH_SIZE = 100
        for i in range(0, len(splits), BATCH_SIZE):
            batch = splits[i:i + BATCH_SIZE]
            for doc in batch:
                doc.metadata['file_id'] = file_id
            vectorstore.add_documents(batch)
            gc.collect()

        # Persist the vectorstore after adding documents
        vectorstore.persist()
        print(f"Successfully indexed {len(splits)} chunks for file_id {file_id}")
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        if 'ids' in docs:
            print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")
        else:
            print(f"No document chunks found for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id})
        # Persist after deletion
        vectorstore.persist()
        print(f"Deleted all documents with file_id {file_id}")

        gc.collect()
        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False
