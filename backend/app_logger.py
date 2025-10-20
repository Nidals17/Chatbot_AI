# backend/app_logger.py
import logging
import os
from datetime import datetime

# --- Ensure logs directory exists ---
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# --- Log file with timestamp ---
log_filename = datetime.now().strftime("chatbot_%Y-%m-%d.log")
log_filepath = os.path.join(LOG_DIR, log_filename)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] → %(message)s",
    handlers=[
        logging.FileHandler(log_filepath, encoding="utf-8"),
        logging.StreamHandler()  # Print to console
    ]
)

# --- Application-wide logger ---
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)

# Optional: add different levels for debugging during development
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

logger.info("✅ Logger initialized successfully")
