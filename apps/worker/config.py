import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from .env
    )
    
    # File Paths
    LOCK_PATH: str = r"C:\XHive\locks\x_session.lock"
    DATA_PATH: str = r"C:\XHive\data"
    BROWSER_DATA_DIR: str = r"C:\XHive\browser_data"
    COOKIE_PATH: str = r"C:\XHive\data\x_cookies.json"
    
    # Application Settings
    WORKER_PORT: int = 8765
    CHROME_HEADLESS: bool = False
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Gemini Configuration
    GEMINI_API_KEY: str = ""


# Create settings instance
settings = Settings()

# Export individual variables for backward compatibility
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID
OPENAI_API_KEY = settings.OPENAI_API_KEY
GEMINI_API_KEY = settings.GEMINI_API_KEY
LOCK_PATH = settings.LOCK_PATH
DATA_PATH = settings.DATA_PATH
BROWSER_DATA_DIR = settings.BROWSER_DATA_DIR
COOKIE_PATH = settings.COOKIE_PATH
WORKER_PORT = settings.WORKER_PORT
CHROME_HEADLESS = settings.CHROME_HEADLESS

# Validate Telegram config
if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set in .env")
if not TELEGRAM_CHAT_ID:
    logger.warning("⚠️ TELEGRAM_CHAT_ID not set in .env")

# Validate Gemini config
if not GEMINI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not set in .env")