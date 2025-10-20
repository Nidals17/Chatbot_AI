import os
import tempfile
import time
import json
import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from backend.config import settings
import glob


PERSIST_DIR = settings.chroma_base_dir 
os.makedirs(PERSIST_DIR, exist_ok=True)

def load_previous_metadata(persist_directory=PERSIST_DIR):
    meta_path = os.path.join(persist_directory, "rag_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        st.session_state.rag_files = {name: None for name in meta.get("files", [])}
        st.session_state.embedding_done = True
        st.session_state.progress = 100
        st.info(f"📦 Loaded {len(st.session_state.rag_files)} files from previous session.")
    else:
        st.session_state.embedding_done = False
        st.session_state.progress = 0


def list_existing_databases(base_dir=PERSIST_DIR):
    if not os.path.exists(base_dir):
        return []
    return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]


def load_chroma_db(persist_directory=PERSIST_DIR):
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"}
    )
    db = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    return db, embeddings


def process_and_add_files(files, persist_directory=PERSIST_DIR):
    db, _ = load_chroma_db(persist_directory)
    all_docs = []
    total_chunks = 0
    processed_chunks = 0

    for file in files:
        file_ext = os.path.splitext(file.name)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file.read())
            tmp_file_path = tmp_file.name

        try:
            loader = PyPDFLoader(tmp_file_path) if file_ext == ".pdf" else TextLoader(tmp_file_path)
            docs = loader.load()
        except Exception as e:
            st.error(f"❌ Failed to process {file.name}: {str(e)}")
            continue

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(docs)
        total_chunks += len(split_docs)
        all_docs.extend(split_docs)

    if total_chunks == 0:
        st.warning("⚠️ No valid text found in uploaded documents.")
        return "No chunks to embed."

    progress_bar = st.progress(0)
    status_text = st.empty()
    start = time.time()
    batch_size = 30

    for i in range(0, len(all_docs), batch_size):
        batch = all_docs[i:i + batch_size]
        db.add_documents(batch)
        processed_chunks += len(batch)

        progress = int((processed_chunks / total_chunks) * 100)
        elapsed = time.time() - start
        remaining = (elapsed / processed_chunks) * (total_chunks - processed_chunks)
        progress_bar.progress(progress)
        status_text.text(
            f"🔢 Embedding chunks... {progress}% complete "
            f"({processed_chunks}/{total_chunks}) | ⏱️ ~{int(remaining)}s left"
        )
        time.sleep(0.2)

    progress_bar.progress(100)
    status_text.text("✅ All embeddings created and saved!")

    meta_path = os.path.join(persist_directory, "rag_metadata.json")
    os.makedirs(persist_directory, exist_ok=True)
    meta = {
        "files": [file.name for file in files],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_chunks": total_chunks
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f)

    del db

    # Clean temp files
    for tmp in glob.glob(tempfile.gettempdir() + "/*"):
        try:
            os.remove(tmp)
        except:
            pass

    return f"✅ Added {total_chunks} chunks to the vector database."


def query_rag(question, persist_directory=PERSIST_DIR, k=3):
    db, _ = load_chroma_db(persist_directory)
    results = db.similarity_search(question, k=k)
    return "\n\n".join([doc.page_content for doc in results])
