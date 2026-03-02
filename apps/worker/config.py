import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Resolve AppData base directory
# - Production: worker runs from %APPDATA%\XHive\worker → base = %APPDATA%\XHive
# - Dev: worker runs from repo → base = C:\XHive (fallback)
_appdata = os.environ.get("APPDATA", "")
_appdata_base = Path(_appdata) / "XHive" if _appdata else Path(r"C:\XHive")

# Load .env — check AppData first, then local
_env_appdata = _appdata_base / "worker" / ".env"
_env_local = Path(__file__).parent / ".env"
_env_path = _env_appdata if _env_appdata.exists() else _env_local
load_dotenv(dotenv_path=_env_path)

# Cookie file: check AppData worker dir first, then local
_cookie_appdata = _appdata_base / "worker" / "cookies" / "twitter.json"
_cookie_local = Path(__file__).parent / "cookies" / "twitter.json"
_default_cookie_path = str(_cookie_appdata if _cookie_appdata.exists() else _cookie_local)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from .env
    )

    # File Paths — default to %APPDATA%\XHive, overridable via .env
    LOCK_PATH: str = str(_appdata_base / "locks" / "x_session.lock")
    DATA_PATH: str = str(_appdata_base / "data")
    BROWSER_DATA_DIR: str = str(_appdata_base / "browser_data")
    COOKIE_PATH: str = _default_cookie_path
    
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