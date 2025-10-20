import streamlit as st
import pandas as pd
import os, sys
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # two levels up -> project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
from backend.rag_engine import list_existing_databases
from backend.config import settings


BASE_DIR = settings.chroma_base_dir
os.makedirs(BASE_DIR, exist_ok=True)

st.set_page_config(page_title="RAG Configuration", page_icon="📂")
st.title("📂 RAG Configuration")

# --- 1️⃣ Initialize session state ---
if "use_rag" not in st.session_state:
    st.session_state.use_rag = "No"
if "active_db" not in st.session_state:
    st.session_state.active_db = None

# --- 2️⃣ Choice: Use RAG or not ---
use_rag_options = ["No", "Yes"]

# Safely set current index
current_value = st.session_state.get("use_rag", "No")
if current_value in use_rag_options:
    current_index = use_rag_options.index(current_value)
else:
    current_index = 0

use_rag = st.radio(
    "Do you want to use RAG?",
    options=use_rag_options,
    index=current_index,
    horizontal=True
)
st.session_state.use_rag = use_rag

# --- 3️⃣ If user activates RAG ---
if use_rag == "Yes":
    st.subheader("🧠 Select a Knowledge Base")

    dbs = list_existing_databases(BASE_DIR)

    previous_db = st.session_state.get("active_db_name", None)

    if not dbs:
        st.warning("⚠️ No databases found. Please create one in the Database Manager page.")
    else:
        selected_db = st.selectbox(
            "Choose a database to use:",
            dbs,
            index=dbs.index(previous_db) if previous_db in dbs else 0,
            key="rag_db_select"
        )

        # Save in session_state when changed
        if selected_db != previous_db:
            st.session_state.active_db_name = selected_db
            st.session_state.active_db = os.path.join(BASE_DIR, selected_db)
            st.success(f"✅ Using database: {selected_db}")

            # Display info
            with st.expander("📊 Database Details"):
                meta_path = Path(st.session_state.active_db) / "rag_metadata.json"
                if meta_path.exists():
                    with open(meta_path) as f:
                        meta = json.load(f)
                    st.write(f"**Database Name:** {Path(st.session_state.active_db).name}")
                    st.write(f"**Files:** {', '.join(meta.get('files', []))}")
                    st.write(f"**Created At:** {meta.get('created_at', 'Unknown')}")
                    st.write(f"**Total Chunks:** {meta.get('total_chunks', 0)}")
                else:
                    st.write("⚠️ No metadata available for this database.")

# --- 4️⃣ If RAG is off ---
else:
    st.session_state.active_db = None
    st.info("💬 RAG is disabled. The chatbot will use **LLM only**.")
