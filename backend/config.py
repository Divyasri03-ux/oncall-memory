import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY", "").strip()
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "northwind-oncall").strip()

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"
FAST_MODEL = "openai/gpt-oss-20b"

def is_groq_configured() -> bool:
    return bool(GROQ_API_KEY and not GROQ_API_KEY.startswith("gsk_your_"))

def is_hindsight_configured() -> bool:
    return bool(HINDSIGHT_API_KEY and not HINDSIGHT_API_KEY.startswith("your_"))
