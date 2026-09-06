import argparse
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler
from config import Settings
from storage import Storage
from sources import collect_items, download_image
from ai import generate
from publisher import TelegramPublisher


def run_once(settings: Settings):
    os.makedirs(settings.media_dir, exist_ok=True)
    store = Storage(settings.db_path)
    items = [x for x in collect_items(settings.rss_feeds, settings.max_source_items) if not store.already_used(x.url)]
    if not items:
        print("No new source items.")
        return
    result = generate(settings.content_prompt, items, settings.openai_api_key, settings.openai_api_base, settings.ai_model)
    source_url = items[0].url
    caption = f"{result['title']}\n\n{result['caption']}\n\nالمصدر: {source_url}"
    media_path = settings.video_path if settings.video_path and os.path.exists(settings.video_path) else ""
    if not media_path and items[0].image_url:
        media_path = os.path.join(settings.media_dir, "latest.jpg")
        if not download_image(items[0].image_url, media_path):
            media_path = ""
    status = TelegramPublisher(settings.telegram_bot_token, settings.telegram_chat_id, settings.dry_run).publish(caption, media_path or None)
    store.save(result["title"], caption, source_url, media_path, status)
    print(f"[{status}] {result['title']}\n{caption}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Generate and publish one post now")
    args = parser.parse_args()
    settings = Settings()
    settings.validate()
    if args.once:
        run_once(settings)
        return
    hour, minute = (int(x) for x in settings.post_time.split(":", 1))
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.timezone))
    scheduler.add_job(lambda: run_once(settings), "cron", hour=hour, minute=minute, id="daily-post", coalesce=True, max_instances=1)
    print(f"{settings.agent_name} scheduled daily at {settings.post_time} ({settings.timezone}); dry_run={settings.dry_run}")
    scheduler.start()

if __name__ == "__main__":
    main()
