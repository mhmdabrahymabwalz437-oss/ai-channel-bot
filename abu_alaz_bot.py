#!/usr/bin/env python3
"""ABU ALAZ manager channel - single-file Telegram content agent.

Required packages:
  pip install requests python-dotenv feedparser apscheduler beautifulsoup4 instaloader tzdata

Run one post:
  python abu_alaz_bot.py --once

Run continuously every 30 minutes:
  python abu_alaz_bot.py
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PROMPT = """أنت وكيل محتوى عربي متخصص في البرمجة والأمن السيبراني والهكر الأخلاقي. أنشئ منشورًا أصليًا وقصيرًا ومفيدًا اعتمادًا على المصادر المتاحة. نوّع بين شرح مفاهيم البرمجة، نصائح كتابة كود آمن، أخبار الثغرات والتحديثات الأمنية، التوعية بالتصيد والهندسة الاجتماعية، وأساسيات اختبار الاختراق المصرّح به. اكتب عنوانًا جذابًا وكابشنًا منظمًا بالعربية مع كلمات تقنية بالإنجليزية عند الحاجة و3 إلى 5 هاشتاجات مناسبة. لا تنسخ المصدر، واذكر رابط المصدر. التزم بالاستخدام القانوني والأخلاقي: لا تقدم تعليمات لاختراق حسابات أو أجهزة أو شبكات دون تصريح، ولا برمجيات خبيثة، ولا سرقة بيانات، ولا تجاوز حماية؛ عند تناول موضوع هجومي حوّله إلى شرح دفاعي أو مختبر آمن مصرح به. أخرج JSON يحتوي على title وcaption فقط."""

DEFAULT_TOPICS = (
    "Python وكتابة كود نظيف",
    "أمن الحسابات والتصيد الإلكتروني",
    "الهكر الأخلاقي داخل مختبر مصرح",
    "أخبار الثغرات والتحديثات الأمنية",
    "أدوات المطورين والأمن السيبراني",
    "الشبكات وحماية الخوادم",
)


@dataclass(frozen=True)
class Settings:
    agent_name: str = os.getenv("AGENT_NAME", "ABU ALAZ manager channel")
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    gemini_key: str = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    gemini_base: str = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/")
    ai_model: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    prompt: str = os.getenv("CONTENT_PROMPT", DEFAULT_PROMPT)
    timezone: str = os.getenv("TIMEZONE", "Africa/Cairo")
    interval: int = int(os.getenv("POST_INTERVAL_MINUTES", "30"))
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes"}
    rss_feeds: tuple[str, ...] = tuple(x.strip() for x in os.getenv("RSS_FEEDS", "").split(",") if x.strip())
    topics: tuple[str, ...] = tuple(x.strip() for x in os.getenv("CONTENT_TOPICS", ",".join(DEFAULT_TOPICS)).split(",") if x.strip())
    media_dir: str = os.getenv("MEDIA_DIR", "media")
    video_path: str = os.getenv("VIDEO_PATH", "")
    db_path: str = os.getenv("DB_PATH", "bot.db")
    max_items: int = int(os.getenv("MAX_SOURCE_ITEMS", "8"))
    instagram_profiles: tuple[str, ...] = tuple(x.strip().lstrip("@").lower() for x in os.getenv("INSTAGRAM_PROFILES", "").split(",") if x.strip())
    instagram_rights: bool = os.getenv("INSTAGRAM_RIGHTS_CONFIRMED", "false").lower() in {"1", "true", "yes"}

    def validate(self) -> None:
        missing = []
        for name, value in (("TELEGRAM_BOT_TOKEN", self.telegram_token), ("TELEGRAM_CHAT_ID", self.telegram_chat_id), ("GEMINI_API_KEY", self.gemini_key), ("CONTENT_PROMPT", self.prompt)):
            if not value or "ضع_" in value:
                missing.append(name)
        if not self.topics:
            raise ValueError("CONTENT_TOPICS cannot be empty")
        if self.interval < 1:
            raise ValueError("POST_INTERVAL_MINUTES must be at least 1")
        if missing:
            raise ValueError("Missing required settings: " + ", ".join(missing))


@dataclass
class Item:
    title: str
    url: str
    summary: str
    image_url: str = ""


class Store:
    def __init__(self, path: str):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, created_at TEXT, title TEXT, caption TEXT, source_url TEXT UNIQUE, media_path TEXT, status TEXT)")

    def used(self, url: str) -> bool:
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT 1 FROM posts WHERE source_url=?", (url,)).fetchone() is not None

    def save(self, title: str, caption: str, url: str, media: str, status: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR IGNORE INTO posts(created_at,title,caption,source_url,media_path,status) VALUES(?,?,?,?,?,?)", (datetime.utcnow().isoformat(), title, caption, url, media, status))


def collect_rss(feeds: tuple[str, ...], limit: int) -> list[Item]:
    result: list[Item] = []
    for url in feeds:
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "abu-alaz-bot/1.0"})
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            for entry in parsed.entries[:limit]:
                html = entry.get("summary", "")
                soup = BeautifulSoup(html, "html.parser")
                image_url = ""
                media = entry.get("media_content", []) or entry.get("enclosures", [])
                if media:
                    image_url = media[0].get("url", "")
                if not image_url and soup.find("img"):
                    image_url = soup.find("img").get("src", "")
                result.append(Item(entry.get("title", ""), entry.get("link", ""), soup.get_text(" ", strip=True), image_url))
        except requests.RequestException as exc:
            print(f"RSS skipped: {url} ({exc})", flush=True)
    return result[:limit]


def download_image(url: str, path: str) -> bool:
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "abu-alaz-bot/1.0"})
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/"):
            return False
        Path(path).write_bytes(response.content)
        return True
    except requests.RequestException:
        return False


def download_instagram_reel(settings: Settings) -> tuple[Item, str] | None:
    if not settings.instagram_profiles or not settings.instagram_rights:
        return None
    try:
        import instaloader
    except ImportError:
        print("Instaloader unavailable; skipping Instagram source", flush=True)
        return None
    root = Path(settings.media_dir)
    root.mkdir(parents=True, exist_ok=True)
    loader = instaloader.Instaloader(
        dirname_pattern=str(root / "{profile}"), filename_pattern="{date_utc}_UTC_{shortcode}",
        download_comments=False, save_metadata=False, compress_json=False, post_metadata_txt_pattern="",
    )
    for username in settings.instagram_profiles:
        try:
            profile = instaloader.Profile.from_username(loader.context, username)
            for post in profile.get_posts():
                if not post.is_video:
                    continue
                folder = root / username
                before = set(folder.rglob("*.mp4")) if folder.exists() else set()
                loader.download_post(post, target=username)
                created = [p for p in folder.rglob("*.mp4") if p not in before]
                if created:
                    item = Item(post.caption.splitlines()[0][:120] if post.caption else f"Instagram Reel من @{username}", f"https://www.instagram.com/p/{post.shortcode}/", post.caption or "")
                    return item, str(created[0])
        except Exception as exc:
            print(f"Instagram skipped for @{username}: {exc}", flush=True)
    return None


def parse_json(text: str) -> dict:
    clean = text.strip().replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    if start >= 0:
        clean = clean[start:]
    return json.loads(clean)


def generate(settings: Settings, items: list[Item]) -> dict:
    sources = "\n".join(f"- {x.title}: {x.summary[:500]} ({x.url})" for x in items)
    request = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "أنت محرر محتوى عربي. أخرج JSON صحيحًا بالمفتاحين title وcaption فقط، دون Markdown."},
            {"role": "user", "content": f"{settings.prompt}\n\nالمصادر أو المحور:\n{sources}"},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }
    endpoint = settings.gemini_base.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {settings.gemini_key}", "Content-Type": "application/json"}
    response = requests.post(endpoint, headers=headers, json=request, timeout=90)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        data = parse_json(content)
    except json.JSONDecodeError:
        request["messages"][-1]["content"] = f"أعد النتيجة كـ JSON صحيح في سطر واحد بالمفتاحين title وcaption فقط. الموضوع والمصادر:\n{sources}"
        retry = requests.post(endpoint, headers=headers, json=request, timeout=90)
        retry.raise_for_status()
        data = parse_json(retry.json()["choices"][0]["message"]["content"])
    if not isinstance(data.get("title"), str) or not isinstance(data.get("caption"), str):
        raise ValueError("Gemini response must contain title and caption")
    return data


def publish(settings: Settings, caption: str, media: str | None) -> str:
    if settings.dry_run:
        return "dry-run"
    base = f"https://api.telegram.org/bot{settings.telegram_token}"
    if media:
        path = Path(media)
        if path.suffix.lower() in {".mp4", ".mov", ".m4v"}:
            if path.stat().st_size > 50 * 1024 * 1024:
                raise ValueError("Telegram video limit is 50 MB")
            endpoint, field, timeout = "/sendVideo", "video", 120
            data = {"chat_id": settings.telegram_chat_id, "caption": caption, "supports_streaming": "true"}
        else:
            endpoint, field, timeout = "/sendPhoto", "photo", 60
            data = {"chat_id": settings.telegram_chat_id, "caption": caption}
        with path.open("rb") as file_handle:
            response = requests.post(base + endpoint, data=data, files={field: file_handle}, timeout=timeout)
    else:
        response = requests.post(base + "/sendMessage", data={"chat_id": settings.telegram_chat_id, "text": caption}, timeout=30)
    if not response.ok:
        try:
            reason = response.json().get("description", response.text[:300])
        except ValueError:
            reason = response.text[:300]
        raise RuntimeError(f"Telegram API rejected request ({response.status_code}): {reason}")
    return "published"


def run_once(settings: Settings) -> None:
    print(f"[{settings.agent_name}] starting one-shot run", flush=True)
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    store = Store(settings.db_path)
    print("[1/4] Reading sources...", flush=True)
    items = [x for x in collect_rss(settings.rss_feeds, settings.max_items) if not store.used(x.url)]
    instagram = download_instagram_reel(settings)
    if instagram and not store.used(instagram[0].url):
        items.insert(0, instagram[0])
    media = instagram[1] if instagram and items and items[0].url == instagram[0].url else ""
    if not items:
        slot = int(time.time()) // (settings.interval * 60)
        topic = settings.topics[slot % len(settings.topics)]
        url = f"internal://topic/{slot}"
        if store.used(url):
            print("This interval was already published.", flush=True)
            return
        items = [Item(f"محور تعليمي: {topic}", url, f"اكتب منشورًا أصليًا تعليميًا عن {topic}.")]
        print(f"No new external source; rotating topic: {topic}", flush=True)
    print(f"[2/4] New source items: {len(items)}", flush=True)
    print("[3/4] Generating with Gemini...", flush=True)
    result = generate(settings, items)
    source_url = items[0].url
    caption = f"{result['title']}\n\n{result['caption']}\n\nالمصدر: {source_url}"
    if not media and settings.video_path and Path(settings.video_path).exists():
        media = settings.video_path
    if not media and items[0].image_url:
        image_path = str(Path(settings.media_dir) / "latest.jpg")
        if download_image(items[0].image_url, image_path):
            media = image_path
    print(f"[4/4] Publishing (dry_run={settings.dry_run})...", flush=True)
    status = publish(settings, caption, media or None)
    store.save(result["title"], caption, source_url, media, status)
    print(f"[{status}] {result['title']}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="ABU ALAZ manager channel")
    parser.add_argument("--once", action="store_true", help="run one post now")
    args = parser.parse_args()
    settings = Settings()
    settings.validate()
    if args.once:
        run_once(settings)
        return
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.timezone))

    def safe_run() -> None:
        try:
            run_once(settings)
        except Exception as exc:
            print(f"Run failed; scheduler continues: {type(exc).__name__}: {exc}", flush=True)

    scheduler.add_job(safe_run, "interval", minutes=settings.interval, id="recurring-post", next_run_time=datetime.now(ZoneInfo(settings.timezone)), coalesce=True, max_instances=1)
    print(f"{settings.agent_name} running every {settings.interval} minutes ({settings.timezone}); dry_run={settings.dry_run}", flush=True)
    scheduler.start()


if __name__ == "__main__":
    main()
