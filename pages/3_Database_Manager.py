# frontend/pages/Database_Manager.py
import streamlit as st
import os
import sys
from pathlib import Path
import zipfile
import tempfile
import io
import json

# Make project root importable when Streamlit runs pages in isolation.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# backend imports
from backend.rag_engine import process_and_add_files, list_existing_databases
from backend.config import settings

# Shared base directory
BASE_DIR = str(settings.chroma_base_dir)
os.makedirs(BASE_DIR, exist_ok=True)

st.set_page_config(page_title="Database Manager", page_icon="🗄️")
st.title("🗄️ RAG Database Manager")

# --- Helpers ---
def get_db_list():
    return list_existing_databases(BASE_DIR)


def meta_exists(db_name: str):
    """Return True if rag_metadata.json exists for db_name."""
    meta_path = Path(BASE_DIR) / db_name / "rag_metadata.json"
    return meta_path.exists()


def read_meta(db_name: str):
    meta_path = Path(BASE_DIR) / db_name / "rag_metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _make_fileobj_from_path(path: str):
    b = open(path, "rb").read()
    bio = io.BytesIO(b)
    bio.name = os.path.basename(path)
    return bio


# --- Sidebar ---
st.sidebar.subheader("📚 Existing Databases")
existing_dbs = get_db_list()
if existing_dbs:
    for db in existing_dbs:
        st.sidebar.write(f"• {db}")
else:
    st.sidebar.info("No databases found yet.")

# --- Tabs ---
tab1, tab2 = st.tabs(["➕ Create Database", "🗑️ Delete Database"])

# --- 1️⃣ Create New Database ---
with tab1:
    st.subheader("➕ Create a New Database")
    new_db_name = st.text_input("Enter a name for your new database:")

    # Check if DB already exists
    db_path = Path(BASE_DIR) / new_db_name if new_db_name else None
    db_already_exists = new_db_name and db_path.exists() and meta_exists(new_db_name)

    if new_db_name and db_already_exists:
        st.warning(f"⚠️ A database named **'{new_db_name}'** already exists.")
        meta = read_meta(new_db_name)
        if meta:
            st.write("**Database details:**")
            st.write(f"- Files: {', '.join(meta.get('files', []))}")
            st.write(f"- Created at: {meta.get('created_at', 'Unknown')}")
            st.write(f"- Total chunks: {meta.get('total_chunks', 0)}")
        st.info("Please choose a different name to create a new database.")
    else:
        uploaded_files = st.file_uploader(
            "Upload files or a zipped folder for this database (PDF / TXT / ZIP)",
            type=["pdf", "txt", "zip"],
            accept_multiple_files=True,
        )

        files_for_embedding = []
        extracted_filenames = []

        if uploaded_files:
            with tempfile.TemporaryDirectory() as tmpdir:
                for uploaded in uploaded_files:
                    name = uploaded.name.lower()
                    if name.endswith(".zip"):
                        try:
                            zip_temp_path = os.path.join(tmpdir, uploaded.name)
                            with open(zip_temp_path, "wb") as f:
                                f.write(uploaded.read())
                            with zipfile.ZipFile(zip_temp_path, "r") as zf:
                                for member in zf.namelist():
                                    if member.lower().endswith((".pdf", ".txt")):
                                        extracted_path = zf.extract(member, path=tmpdir)
                                        fo = _make_fileobj_from_path(extracted_path)
                                        files_for_embedding.append(fo)
                                        extracted_filenames.append(fo.name)
                        except Exception as e:
                            st.error(f"❌ Error reading zip {uploaded.name}: {e}")
                    else:
                        try:
                            uploaded.seek(0)
                            b = uploaded.read()
                            bio = io.BytesIO(b)
                            bio.name = uploaded.name
                            files_for_embedding.append(bio)
                            extracted_filenames.append(bio.name)
                        except Exception as e:
                            st.warning(f"Could not read uploaded file {uploaded.name}: {e}")

            st.success(f"✅ Prepared {len(files_for_embedding)} file(s) for embedding.")
            for fn in extracted_filenames:
                st.write(f"- {fn}")

        if st.button("⚙️ Create Embeddings"):
            if not new_db_name:
                st.error("Please enter a name for the database.")
            elif not uploaded_files:
                st.error("Please upload at least one file or zip.")
            else:
                db_path.mkdir(parents=True, exist_ok=True)
                st.info(f"Creating embeddings for **{new_db_name}**...")

                try:
                    result_msg = process_and_add_files(files_for_embedding, persist_directory=str(db_path))
                    st.success(result_msg)
                    st.session_state.selected_db = new_db_name
                    st.success(f"✅ Database '{new_db_name}' created successfully!")
                except Exception as e:
                    st.exception(f"❌ Error while creating embeddings: {e}")

                st.rerun()


# --- Delete Database ---
with tab2:
    st.subheader("🗑️ Delete a Database")
    existing_dbs = get_db_list()
    if existing_dbs:
        del_db = st.selectbox("Select a database to delete:", existing_dbs)
        if st.button("🗑️ Delete Database"):
            import shutil
            try:
                shutil.rmtree(Path(BASE_DIR) / del_db)
                st.success(f"✅ Database '{del_db}' deleted.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not delete '{del_db}': {e}")
    else:
        st.info("No databases to delete.")
