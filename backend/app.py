from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import openai
import time
import google.generativeai as genai
from backend.rag_engine import query_rag
from backend.config import settings
from backend.app_logger import logger


# ============================================================
# 🚀 Initialize App
# ============================================================
app = FastAPI(title="LLM Chatbot API", version="1.1")


# ============================================================
# 🧩 Data Models
# ============================================================
class LLMRequest(BaseModel):
    """Incoming payload for any LLM query."""
    model_name: str
    api_key: str
    prompt: str
    system_message: Optional[str] = "You are a helpful AI assistant."
    chat_history: list = []
    use_rag: bool = False
    db_path: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class LLMResponse(BaseModel):
    """Standardized response for chatbot."""
    response: str
    success: bool
    error_message: Optional[str] = None


# ============================================================
# ⚙️ Helper: Clean API error messages
# ============================================================
def parse_api_error(provider: str, error: Exception) -> str:
    """Return a user-friendly message for known API errors."""
    err_msg = str(error).lower()

    if "401" in err_msg or "invalid api key" in err_msg or "authentication" in err_msg:
        return f"❌ Invalid API key. Please check your {provider} API key."
    elif "quota" in err_msg or "limit" in err_msg:
        return f"⚠️ {provider} API quota exceeded. Please check your account limits."
    else:
        return f"❌ {provider} API error: {str(error)}"


# ============================================================
# 🤖 LLM Integrations
# ============================================================
def get_deepseek_llm(api_key, prompt, system_message, chat_history, temperature, max_tokens):
    """DeepSeek API (OpenAI-compatible)."""
    try:
        client = openai.OpenAI(api_key=api_key, base_url=settings.deepseek_base_url)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content, True, None

    except Exception as e:
        return None, False, parse_api_error("DeepSeek", e)


def get_gemini_llm(api_key, prompt, system_message, chat_history):
    """Google Gemini integration."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        # Construct full prompt
        full_prompt = ""
        if system_message:
            full_prompt += f"System: {system_message}\n\n"
        if chat_history:
            for msg in chat_history:
                role = "Human" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
        full_prompt += f"Human: {prompt}\nAssistant:"

        response = model.generate_content(full_prompt)
        if response.text:
            return response.text, True, None
        else:
            return None, False, "⚠️ Gemini returned an empty response."

    except Exception as e:
        return None, False, parse_api_error("Gemini", e)


def get_openai_llm(api_key, prompt, system_message, chat_history, temperature, max_tokens):
    """OpenAI ChatGPT API integration."""
    try:
        client = openai.OpenAI(api_key=api_key)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content, True, None

    except Exception as e:
        return None, False, parse_api_error("OpenAI", e)


# ============================================================
# 🎯 Main LLM Endpoint (with graceful fallbacks)
# ============================================================
@app.post("/query_llm", response_model=LLMResponse)
async def query_llm(request: LLMRequest):
    """
    Unified endpoint for querying any supported LLM.
    Automatically instructs the model to respond gracefully
    when input is nonsense or unrelated.
    """

    logger.info(f"📥 Request | Model: {request.model_name} | RAG: {request.use_rag}")

    # --- Validation ---
    if not request.api_key.strip():
        return LLMResponse(success=False, response="", error_message="❌ API key is required.")
    if not request.prompt.strip():
        return LLMResponse(success=False, response="", error_message="❌ Prompt cannot be empty.")

    prompt = request.prompt.strip()

    # --- Inject Safety Behavior into System Message ---
    safe_instruction = (
        "If the question is unclear, nonsensical, or unrelated to the topic, "
        "respond politely with an apology or request clarification. "
        "If RAG context is empty, explain that you couldn’t find relevant info "
        "instead of repeating old answers."
    )
    system_message = f"{request.system_message}\n\n{safe_instruction}"

    # --- Apply RAG Context ---
    if request.use_rag:
        if not request.db_path:
            logger.warning("⚠️ RAG is enabled but no database path provided.")
        else:
            try:
                context = query_rag(prompt, persist_directory=request.db_path)
                prompt = f"Use the following context to answer:\n\n{context}\n\nQuestion: {prompt}"
            except Exception as e:
                logger.exception(f"RAG retrieval failed: {e}")
                return LLMResponse(
                    success=False,
                    response="",
                    error_message=f"⚠️ RAG Error: Could not retrieve context. Details: {str(e)}",
                )

    # --- Route to correct LLM ---
    start_time = time.time()
    try:
        text, ok, err = None, False, None

        if request.model_name == "DeepSeek":
            text, ok, err = get_deepseek_llm(
                request.api_key, prompt, system_message, request.chat_history,
                request.temperature, request.max_tokens
            )
        elif request.model_name == "Gemini":
            text, ok, err = get_gemini_llm(
                request.api_key, prompt, system_message, request.chat_history
            )
        elif request.model_name == "ChatGPT":
            text, ok, err = get_openai_llm(
                request.api_key, prompt, system_message, request.chat_history,
                request.temperature, request.max_tokens
            )
        else:
            return LLMResponse(success=False, response="", error_message=f"❌ Unknown model: {request.model_name}")

        latency = round(time.time() - start_time, 2)

        if ok and text:
            logger.info(f"✅ Success | Model: {request.model_name} | {latency}s")
            return LLMResponse(success=True, response=text)
        else:
            logger.warning(f"⚠️ Query failed | {err or 'No text returned'} | {latency}s")
            return LLMResponse(success=False, response="", error_message=err or "No valid response generated.")

    except Exception as e:
        latency = round(time.time() - start_time, 2)
        logger.exception(f"❌ Exception | Model: {request.model_name} | {latency}s | Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


# ============================================================
# 🩺 Health & Root Endpoints
# ============================================================
@app.get("/health")
async def health_check():
    """Simple endpoint to verify backend health."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint for quick status check."""
    return {"message": "✅ LLM Chatbot API is running successfully!"}
