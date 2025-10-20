import streamlit as st
import asyncio
import httpx
import os

# ============================================================
# ⚙️ Page Setup
# ============================================================
st.set_page_config(page_title="Chatbot", page_icon="💬")
st.title("💬 Chatbot Application")

# ============================================================
# 🧩 Initialize Session State Safely
# ============================================================
defaults = {
    "llm_choice": None,
    "api_key": "",
    "use_rag": None,
    "active_db": None,
    "rag_files": {},
    "chat_history": [],
    "system_message": "You are a helpful AI assistant.",
    "temperature": 0.7,
    "max_tokens": 1000,
    "last_rag_state": None,
    "last_payload": None,  # 👈 New: avoid re-sending same message
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ============================================================
# ⚙️ Async Backend Helper
# ============================================================
async def ask_backend(payload):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/query_llm",
            json=payload,
            timeout=60
        )
        return response


# ============================================================
# 🧠 Pre-run Validations
# ============================================================
llm_ready = st.session_state.llm_choice and st.session_state.api_key.strip()
rag_ready = st.session_state.use_rag in ["No", "Yes"]
rag_enabled = st.session_state.use_rag == "Yes"
has_db = bool(st.session_state.active_db)

if not llm_ready:
    st.warning("⚠️ Go to **LLM** page and select a model + enter your API key.")
elif not rag_ready:
    st.warning("⚠️ Go to **RAG** page and choose whether you want to use RAG.")
elif rag_enabled and not has_db:
    st.warning("⚠️ You enabled RAG but didn’t select a database. Go to the **RAG** page and choose one.")
else:

    # ============================================================
    # 🔄 Detect RAG Mode Switch (and reset chat)
    # ============================================================
    if st.session_state.last_rag_state != st.session_state.use_rag:
        st.session_state.chat_history = []
        st.session_state.last_rag_state = st.session_state.use_rag
        st.info("🧹 Chat history cleared due to RAG mode change.")

    # ============================================================
    # 🔧 Display Current Configuration
    # ============================================================
    with st.expander("🔧 Current Configuration", expanded=False):
        st.write(f"**Model:** {st.session_state.llm_choice}")
        st.write(f"**RAG Enabled:** {st.session_state.use_rag}")
        st.write(f"**System Message:** {st.session_state.system_message}")
        st.write(f"**Temperature:** {st.session_state.temperature}")
        st.write(f"**Max Tokens:** {st.session_state.max_tokens}")

        if rag_enabled:
            st.write(f"**Database:** {os.path.basename(st.session_state.active_db)}")
        else:
            st.write("💡 Using LLM only (no database context).")

    # ============================================================
    # 💬 Chatbot Section
    # ============================================================
    st.subheader("🤖 Chatbot")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

    # --- Display chat history BEFORE new input ---
    chat_container = st.container()
    for role, message in st.session_state.chat_history:
        with chat_container.chat_message(role):
            st.markdown(message)

    # --- User Input ---
    user_message = st.chat_input("Type your message here...")

    if user_message:
        # Avoid accidental double-submit
        new_payload = (user_message, st.session_state.use_rag, st.session_state.llm_choice)
        if new_payload == st.session_state.last_payload:
            st.warning("⚠️ Duplicate message ignored.")
            st.stop()
        st.session_state.last_payload = new_payload

        # Display user message
        with chat_container.chat_message("user"):
            st.markdown(user_message)
        st.session_state.chat_history.append(("user", user_message))

        # --- Prepare payload ---
        payload = {
            "model_name": st.session_state.llm_choice,
            "api_key": st.session_state.api_key,
            "prompt": user_message,
            "system_message": st.session_state.system_message,
            "chat_history": [
                {"role": "user" if role == "user" else "assistant", "content": msg}
                for role, msg in st.session_state.chat_history[:-1]
            ],
            "use_rag": rag_enabled,
            "db_path": st.session_state.get("active_db"),
            "temperature": st.session_state.temperature,
            "max_tokens": st.session_state.max_tokens,
        }

        # --- Query Backend ---
        with chat_container.chat_message("assistant"):
            thinking_area = st.empty()
            thinking_area.markdown("🤔 **Thinking...**")

            try:
                response = asyncio.run(ask_backend(payload))
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        bot_response = result.get("response", "").strip()
                        if not bot_response:
                            bot_response = "🤔 I couldn’t generate a proper answer this time."
                        thinking_area.markdown(bot_response)
                    else:
                        bot_response = result.get("error_message", "⚠️ Unknown error.")
                        thinking_area.error(bot_response)
                else:
                    bot_response = f"❌ Server error (HTTP {response.status_code})."
                    thinking_area.error(bot_response)

            except httpx.ConnectError:
                bot_response = "❌ Cannot connect to backend. Make sure FastAPI is running."
                thinking_area.error(bot_response)
            except httpx.ReadTimeout:
                bot_response = "❌ Request timed out. The backend took too long to respond."
                thinking_area.error(bot_response)
            except Exception as e:
                bot_response = f"❌ Unexpected error: {str(e)}"
                thinking_area.error(bot_response)

        # Append bot response at the end
        st.session_state.chat_history.append(("assistant", bot_response))

    # ============================================================
    # 🧭 Sidebar — Backend Status
    # ============================================================
    with st.sidebar:
        st.subheader("🔌 Backend Status")
        if st.button("Check Backend Connection"):
            try:
                with httpx.Client(timeout=5) as client:
                    response = client.get("http://127.0.0.1:8000/health")
                    if response.status_code == 200:
                        st.success("✅ Backend is running")
                    else:
                        st.error("❌ Backend error")
            except Exception:
                st.error("❌ Backend not reachable")
                st.info("Run `uvicorn backend.app:app --reload`")
