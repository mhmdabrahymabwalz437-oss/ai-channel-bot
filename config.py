from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    ai_model: str = os.getenv("AI_MODEL", "gpt-5-mini")
    content_prompt: str = os.getenv("CONTENT_PROMPT", "")
    language: str = os.getenv("LANGUAGE", "ar")
    timezone: str = os.getenv("TIMEZONE", "Africa/Cairo")
    post_time: str = os.getenv("POST_TIME", "18:00")
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}
    rss_feeds: tuple[str, ...] = tuple(x.strip() for x in os.getenv("RSS_FEEDS", "").split(",") if x.strip())
    media_dir: str = os.getenv("MEDIA_DIR", "media")
    video_path: str = os.getenv("VIDEO_PATH", "")
    db_path: str = os.getenv("DB_PATH", "bot.db")
    max_source_items: int = int(os.getenv("MAX_SOURCE_ITEMS", "8"))
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")

    def validate(self) -> None:
        missing = []
        for key, value in (("TELEGRAM_BOT_TOKEN", self.telegram_bot_token), ("TELEGRAM_CHAT_ID", self.telegram_chat_id), ("OPENAI_API_KEY", self.openai_api_key), ("CONTENT_PROMPT", self.content_prompt)):
            if not value or "ضع_" in value:
                missing.append(key)
        if missing:
            raise ValueError("Missing required settings: " + ", ".join(missing))
