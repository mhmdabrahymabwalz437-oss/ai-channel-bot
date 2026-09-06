from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONTENT_PROMPT = """أنت وكيل محتوى عربي متخصص في البرمجة والأمن السيبراني والهكر الأخلاقي. أنشئ منشورًا أصليًا وقصيرًا ومفيدًا اعتمادًا على المصادر المتاحة. نوّع بين شرح مفاهيم البرمجة، نصائح كتابة كود آمن، أخبار الثغرات والتحديثات الأمنية، التوعية بالتصيد والهندسة الاجتماعية، وأساسيات اختبار الاختراق المصرّح به. اكتب عنوانًا جذابًا وكابشنًا منظمًا بالعربية مع كلمات تقنية بالإنجليزية عند الحاجة و3 إلى 5 هاشتاجات مناسبة. لا تنسخ المصدر، واذكر رابط المصدر. التزم بالاستخدام القانوني والأخلاقي: لا تقدم تعليمات لاختراق حسابات أو أجهزة أو شبكات دون تصريح، ولا برمجيات خبيثة، ولا سرقة بيانات، ولا تجاوز حماية؛ عند تناول موضوع هجومي حوّله إلى شرح دفاعي أو مختبر آمن مصرح به. أخرج JSON يحتوي على title وcaption فقط."""

@dataclass(frozen=True)
class Settings:
    agent_name: str = os.getenv("AGENT_NAME", "ABU ALAZ manager channel")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    openai_api_key: str = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    openai_api_base: str = os.getenv("GEMINI_API_BASE", os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))
    ai_model: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    content_prompt: str = os.getenv("CONTENT_PROMPT", DEFAULT_CONTENT_PROMPT)
    language: str = os.getenv("LANGUAGE", "ar")
    timezone: str = os.getenv("TIMEZONE", "Africa/Cairo")
    post_time: str = os.getenv("POST_TIME", "18:00")
    post_interval_minutes: int = int(os.getenv("POST_INTERVAL_MINUTES", "30"))
    content_topics: tuple[str, ...] = tuple(x.strip() for x in os.getenv("CONTENT_TOPICS", "Python وكتابة كود نظيف,أمن الحسابات والتصيد الإلكتروني,الهكر الأخلاقي داخل مختبر مصرح,أخبار الثغرات والتحديثات الأمنية,أدوات المطورين والأمن السيبراني,الشبكات وحماية الخوادم").split(",") if x.strip())
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}
    rss_feeds: tuple[str, ...] = tuple(x.strip() for x in os.getenv("RSS_FEEDS", "").split(",") if x.strip())
    instagram_profiles: tuple[str, ...] = tuple(x.strip().lstrip("@").lower() for x in os.getenv("INSTAGRAM_PROFILES", "").split(",") if x.strip())
    instagram_rights_confirmed: bool = os.getenv("INSTAGRAM_RIGHTS_CONFIRMED", "false").lower() in {"1", "true", "yes"}
    instagram_login: str = os.getenv("INSTAGRAM_LOGIN", "")
    media_dir: str = os.getenv("MEDIA_DIR", "media")
    video_path: str = os.getenv("VIDEO_PATH", "")
    db_path: str = os.getenv("DB_PATH", "bot.db")
    max_source_items: int = int(os.getenv("MAX_SOURCE_ITEMS", "8"))
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")

    def validate(self) -> None:
        missing = []
        for key, value in (("TELEGRAM_BOT_TOKEN", self.telegram_bot_token), ("TELEGRAM_CHAT_ID", self.telegram_chat_id), ("GEMINI_API_KEY or OPENAI_API_KEY", self.openai_api_key), ("CONTENT_PROMPT", self.content_prompt)):
            if not value or "ضع_" in value:
                missing.append(key)
        if missing:
            raise ValueError("Missing required settings: " + ", ".join(missing))
