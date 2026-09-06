from dataclasses import dataclass
import feedparser
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

@dataclass
class SourceItem:
    title: str
    url: str
    summary: str
    image_url: str = ""


def collect_items(feeds: tuple[str, ...], limit: int) -> list[SourceItem]:
    out = []
    for feed_url in feeds:
        try:
            response = requests.get(feed_url, timeout=20, headers={"User-Agent": "ai-channel-bot/1.0"})
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        except requests.RequestException as exc:
            print(f"RSS source skipped ({feed_url}): {exc}", flush=True)
            continue
        for entry in parsed.entries[:limit]:
            html = entry.get("summary", "")
            soup = BeautifulSoup(html, "html.parser")
            image_url = ""
            media = entry.get("media_content", []) or entry.get("enclosures", [])
            if media:
                image_url = media[0].get("url", "")
            if not image_url:
                image = soup.find("img")
                image_url = image.get("src", "") if image else ""
            out.append(SourceItem(entry.get("title", ""), entry.get("link", ""), soup.get_text(" ", strip=True), image_url))
    return out[:limit]


def download_image(url: str, destination: str) -> bool:
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": "ai-channel-bot/1.0"})
        r.raise_for_status()
        if not r.headers.get("content-type", "").startswith("image/"):
            return False
        open(destination, "wb").write(r.content)
        return True
    except requests.RequestException:
        return False
