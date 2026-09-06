import requests
from pathlib import Path

class TelegramPublisher:
    def __init__(self, token: str, chat_id: str, dry_run: bool = True):
        self.base = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.dry_run = dry_run

    def publish(self, caption: str, media_path: str | None = None) -> str:
        if self.dry_run:
            return "dry-run"
        if media_path:
            path = Path(media_path)
            if path.stat().st_size > 50 * 1024 * 1024:
                raise ValueError("Telegram Bot API video limit is 50 MB")
            if path.suffix.lower() in {".mp4", ".mov", ".m4v"}:
                endpoint = "/sendVideo"
                field = "video"
                data = {"chat_id": self.chat_id, "caption": caption, "supports_streaming": "true"}
                timeout = 120
            else:
                endpoint = "/sendPhoto"
                field = "photo"
                data = {"chat_id": self.chat_id, "caption": caption}
                timeout = 60
            with open(media_path, "rb") as fh:
                r = requests.post(self.base + endpoint, data=data, files={field: fh}, timeout=timeout)
        else:
            r = requests.post(self.base + "/sendMessage", data={"chat_id": self.chat_id, "text": caption}, timeout=30)
        if not r.ok:
            try:
                details = r.json().get("description", r.text[:300])
            except ValueError:
                details = r.text[:300]
            raise RuntimeError(f"Telegram API rejected the request ({r.status_code}): {details}")
        return "published"
