import streamlit as st

st.set_page_config(page_title="LLM Selection", page_icon="🧠")
st.title("Choose Your LLM")

# --- 0. Initialize session state ---
if "llm_choice" not in st.session_state:
    st.session_state.llm_choice = None
if "api_key" not in st.session_state:
    st.session_state.api_key = None

# --- 1. Dropdown to select model ---
st.session_state.llm_choice = st.selectbox(
    "Select a Language Model",
    ["DeepSeek", "Gemini", "ChatGPT"],
    index=["DeepSeek", "Gemini", "ChatGPT"].index(st.session_state.llm_choice) if st.session_state.llm_choice else 0
)

# --- 2. API key input ---
st.session_state.api_key = st.text_input(
    "Enter your API key:",
    value=st.session_state.api_key if st.session_state.api_key else "",
    type="password"
)

if st.session_state.llm_choice and st.session_state.api_key:
    st.success(f"✅ Model selected: {st.session_state.llm_choice}")