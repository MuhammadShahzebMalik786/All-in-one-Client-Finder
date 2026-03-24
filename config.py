import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Central configuration."""

    # LinkedIn
    LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

    # Comma-separated list in .env: OPENROUTER_KEYS=key1,key2,key3
    OPENROUTER_KEYS = [
        key.strip()
        for key in os.getenv("OPENROUTER_KEYS", "").split(",")
        if key.strip()
    ]
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Gemini fallback
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    # Local Model (Ollama) — CPU fallback when APIs fail
    # Download from https://ollama.ai
    # Run: ollama run mistral (or phi for faster, neural-chat for balanced)
    OLLAMA_MODEL = "mistral"  # or "phi" (2.7GB, faster), "neural-chat" (4GB, balanced)
    OLLAMA_BASE_URL = "http://localhost:11434/api"
    OLLAMA_TIMEOUT = 300  # seconds

    # SMTP
    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

    # Your Info
    YOUR_NAME = "Muhammad Shahzeb Malik"
    YOUR_BUSINESS = "Virtual Support Group"
    YOUR_TITLE = "Automation & Product Engineer"
    YOUR_PHONE = "+92 344 897 0498"
    YOUR_WEBSITE = ""

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PORTFOLIO_FILE = os.path.join(BASE_DIR, "portfolio.json")

    # Rate limiting (seconds)
    LINKEDIN_DELAY = 3
    GOOGLE_MAPS_DELAY = 1
    SCRAPE_DELAY = 2
    EMAIL_DELAY = 30

    @classmethod
    def ensure_data_dir(cls):
        os.makedirs(cls.DATA_DIR, exist_ok=True)
