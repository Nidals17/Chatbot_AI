import streamlit as st

st.set_page_config(page_title="System Configuration", page_icon="🎯")
st.title("🎯 System Message Configuration")

# --- 1️⃣ Initialize session state only ONCE (and never overwrite) ---
if "initialized_system_page" not in st.session_state:
    st.session_state.initialized_system_page = True

    # These are created only once, not overwritten every time the page reruns.
    st.session_state.setdefault("system_message", "You are a helpful AI assistant.")
    st.session_state.setdefault("selected_preset", "Default Assistant")
    st.session_state.setdefault("saved_system_messages", {})
    st.session_state.setdefault("temperature", 0.7)
    st.session_state.setdefault("max_tokens", 1000)


# --- 2️⃣ Define presets ---
predefined_messages = {
    "Default Assistant": "You are a helpful AI assistant.",
    "Professional Consultant": """You are a professional AI consultant. Provide well-structured, evidence-based responses. 
    Use formal language, cite sources when possible, and always maintain a professional tone.""",
    "Creative Writer": """You are a creative writing assistant with expertise in storytelling, character development, and narrative techniques. 
    Help users with creative projects, provide imaginative ideas, and offer constructive feedback on writing.""",
    "Code Helper": """You are an expert programming assistant. Provide clean, well-documented code examples with explanations. 
    Help debug issues, suggest best practices, and explain complex programming concepts clearly.""",
    "Patient Teacher": """You are a patient and knowledgeable teacher. Break down complex concepts into simple terms, 
    provide examples and analogies, and always encourage learning. Adapt your explanations to the student's level.""",
    "Casual Friend": """You are a friendly and casual AI companion. Be conversational, supportive, and approachable. 
    Use a warm tone and show empathy. Feel free to use humor when appropriate.""",
    "Research Assistant": """You are a thorough research assistant. Provide comprehensive, well-organized information 
    with proper structure. Always fact-check and present multiple perspectives when relevant.""",
    "Business Advisor": """You are an experienced business advisor. Provide strategic insights, analyze business scenarios, 
    and offer practical solutions. Focus on actionable advice and consider various business aspects.""",
    "Therapist Assistant": """You are a supportive and empathetic assistant trained in active listening. 
    Provide emotional support, ask thoughtful questions, and help users process their thoughts and feelings. 
    Note: Always recommend professional help for serious mental health concerns.""",
    "Debugging Expert": """You are a debugging expert specialized in finding and fixing code issues. 
    Analyze code systematically, identify potential problems, and provide clear solutions with explanations."""
}

# Combine predefined + user-saved
all_message_names = (
    ["Custom"]
    + list(predefined_messages.keys())
    + list(st.session_state.saved_system_messages.keys())
)

# --- 3️⃣ Keep selected preset persistent ---
selected_preset = st.selectbox(
    "Choose a preset:",
    all_message_names,
    index=(
        all_message_names.index(st.session_state.selected_preset)
        if st.session_state.selected_preset in all_message_names
        else 1
    ),
)

# If user changes preset, store it persistently
if selected_preset != st.session_state.selected_preset:
    st.session_state.selected_preset = selected_preset


# --- 4️⃣ Handle the selected preset ---
if selected_preset == "Custom":
    st.session_state.system_message = st.text_area(
        "Enter your custom system message:",
        value=st.session_state.system_message,
        height=150,
        help="Define how your AI assistant should behave.",
    )

    save_name = st.text_input("💾 Save this system message as:", key="save_name", placeholder="e.g. My Teaching Style")
    if st.button("Save System Message"):
        if not save_name:
            st.error("Please provide a name for your system message.")
        else:
            st.session_state.saved_system_messages[save_name] = st.session_state.system_message
            st.success(f"✅ Saved system message as '{save_name}'!")
else:
    # Either a predefined or saved message
    if selected_preset in predefined_messages:
        st.session_state.system_message = predefined_messages[selected_preset]
    else:
        st.session_state.system_message = st.session_state.saved_system_messages[selected_preset]
    st.info(f"Loaded system message: **{selected_preset}**")


# --- 5️⃣ Preview ---
st.subheader("👁️ System Message Preview")
st.code(st.session_state.system_message, language="text")


# --- 4️⃣ Model Parameters (independent) ---
st.subheader("⚙️ Model Parameters (Global Settings)")

col1, col2 = st.columns(2)

with col1:
    st.session_state.temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        step=0.1,
        help="Controls randomness: 0.0 = deterministic, 2.0 = very creative"
    )

with col2:
    st.session_state.max_tokens = st.slider(
        "Max Tokens",
        min_value=100,
        max_value=4000,
        value=st.session_state.max_tokens,
        step=100,
        help="Maximum length of the response"
    )

st.info(f"🌡️ Current temperature: **{st.session_state.temperature}** | ✍️ Max tokens: **{st.session_state.max_tokens}**")