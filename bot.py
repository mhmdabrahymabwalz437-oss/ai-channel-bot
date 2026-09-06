import argparse
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.blocking import BlockingScheduler
from config import Settings
from storage import Storage
from sources import SourceItem, collect_items, download_image
from instagram_source import download_latest_authorized_reel
from ai import generate
from publisher import TelegramPublisher


def run_once(settings: Settings):
    print(f"[{settings.agent_name}] starting one-shot run", flush=True)
    os.makedirs(settings.media_dir, exist_ok=True)
    store = Storage(settings.db_path)
    print("[1/4] Reading sources...", flush=True)
    items = [x for x in collect_items(settings.rss_feeds, settings.max_source_items) if not store.already_used(x.url)]
    print(f"[2/4] New source items: {len(items)}", flush=True)
    instagram_download = download_latest_authorized_reel(
        settings.instagram_profiles,
        settings.media_dir,
        settings.instagram_rights_confirmed,
    )
    if instagram_download and not store.already_used(instagram_download.item.url):
        items.insert(0, instagram_download.item)
    if not items:
        slot = int(datetime.now().timestamp()) // (settings.post_interval_minutes * 60)
        topic = settings.content_topics[slot % len(settings.content_topics)]
        synthetic_url = f"internal://topic/{slot}"
        if store.already_used(synthetic_url):
            print("This interval was already published.", flush=True)
            return
        items = [SourceItem(
            title=f"محور تعليمي: {topic}",
            url=synthetic_url,
            summary=f"أنشئ منشورًا أصليًا تعليميًا عن {topic} دون الحاجة إلى مصدر خارجي.",
        )]
        print(f"No new external source; using rotating topic: {topic}", flush=True)
    print("[3/4] Generating content with Gemini...", flush=True)
    result = generate(settings.content_prompt, items, settings.openai_api_key, settings.openai_api_base, settings.ai_model)
    source_url = items[0].url
    caption = f"{result['title']}\n\n{result['caption']}\n\nالمصدر: {source_url}"
    media_path = settings.video_path if settings.video_path and os.path.exists(settings.video_path) else ""
    if instagram_download and instagram_download.item.url == source_url:
        media_path = instagram_download.media_path
    if not media_path and items[0].image_url:
        media_path = os.path.join(settings.media_dir, "latest.jpg")
        if not download_image(items[0].image_url, media_path):
            media_path = ""
    print(f"[4/4] Publishing (dry_run={settings.dry_run})...", flush=True)
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
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.timezone))
    def safe_run():
        try:
            run_once(settings)
        except Exception as exc:
            print(f"Run failed but scheduler will continue: {type(exc).__name__}: {exc}", flush=True)
    scheduler.add_job(safe_run, "interval", minutes=settings.post_interval_minutes, id="recurring-post", next_run_time=datetime.now(ZoneInfo(settings.timezone)), coalesce=True, max_instances=1)
    print(f"{settings.agent_name} running every {settings.post_interval_minutes} minutes ({settings.timezone}); dry_run={settings.dry_run}", flush=True)
    scheduler.start()

if __name__ == "__main__":
    main()
