from pathlib import Path
from dataclasses import dataclass

from sources import SourceItem


@dataclass
class InstagramDownload:
    item: SourceItem
    media_path: str


def download_latest_authorized_reel(
    profiles: tuple[str, ...],
    destination: str,
    rights_confirmed: bool,
) -> InstagramDownload | None:
    """Download one latest video only from an explicitly authorized profile.

    This uses Instaloader's public-profile flow. It intentionally does not accept
    arbitrary post URLs or credentials, and refuses to run without an explicit
    rights confirmation in the environment.
    """
    if not rights_confirmed or not profiles:
        return None

    try:
        import instaloader
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt to enable Instagram sources") from exc

    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    loader = instaloader.Instaloader(
        dirname_pattern=str(root / "{profile}"),
        filename_pattern="{date_utc}_UTC_{shortcode}",
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
    )

    for username in profiles:
        try:
            profile = instaloader.Profile.from_username(loader.context, username)
            for post in profile.get_posts():
                if not post.is_video:
                    continue
                post_url = f"https://www.instagram.com/p/{post.shortcode}/"
                target_dir = root / username
                before = set(target_dir.rglob("*.mp4")) if target_dir.exists() else set()
                loader.download_post(post, target=username)
                created = [p for p in target_dir.rglob("*.mp4") if p not in before]
                if created:
                    item = SourceItem(
                        title=post.caption.splitlines()[0][:120] if post.caption else f"Instagram Reel من @{username}",
                        url=post_url,
                        summary=post.caption or "",
                    )
                    return InstagramDownload(item=item, media_path=str(created[0]))
        except Exception as exc:
            print(f"Instagram source skipped for @{username}: {exc}")
    return None
