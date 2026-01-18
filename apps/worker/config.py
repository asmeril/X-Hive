from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOCK_PATH: str = r"C:\XHive\locks\x_session.lock"
    DATA_PATH: str = r"C:\XHive\data"
    WORKER_PORT: int = 8765
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
