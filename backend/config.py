from pydantic_settings import BaseSettings
from pathlib import Path
class Settings(BaseSettings):
    # --- General settings ---
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    project_root: Path = Path(__file__).resolve().parent.parent
    chroma_base_dir: Path = project_root / "chroma_dbs"

    # --- DeepSeek ---
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # --- OpenAI (ChatGPT) ---
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"

    # --- Google Gemini ---
    gemini_model: str = "gemini-pro"

    # --- Embedding model ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Logging & Debug ---
    log_level: str = "INFO"
    enable_debug: bool = False



# Create a single instance to import everywhere
settings = Settings()
