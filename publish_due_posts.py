"""
publish_due_posts.py

Folder-based Instagram posting.

How it works
------------
Put one folder per post inside `posts/`:

    posts/2026-10-06 0900 testimonial/
        1.jpg
        2.jpg            <- 2+ images = carousel (up to 10)
        caption.txt      <- the caption (optional)

- The folder name starts with the date and time (UK time) the post should
  go live. A folder with only a date posts at 09:00 that day. A folder with
  no date posts at the next run.
- Folders whose name starts with "draft" or "_" are ignored, so you can
  prepare posts without them going out.
- Images can be JPG, PNG or WEBP. They are converted to JPG automatically
  (Instagram only accepts JPG) and posted in file-name order.

After a post goes out, its folder moves to `posted/` with a result.txt.
If something goes wrong, the folder moves to `failed/` with an error.txt
explaining what to fix, and the run is marked as failed so GitHub emails you.
"""

import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageOps

GRAPH = "https://graph.instagram.com/v21.0"
LONDON = ZoneInfo("Europe/London")
ROOT = Path(__file__).resolve().parent
POSTS, POSTED, FAILED, MEDIA = (ROOT / d for d in ("posts", "posted", "failed", "media"))
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
NAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[ _T-]+(\d{1,2})[:.]?(\d{2}))?")
DRY_RUN = os.getenv("DRY_RUN") == "1"


class PostError(Exception):
    """A problem with one post that the person can fix."""


# ---------- helpers ----------

def log(msg):
    print(msg, flush=True)


def git(*args):
    if DRY_RUN:
        log(f"[dry run] git {' '.join(args)}")
        return ""
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def due_time(folder_name):
    """Return the London datetime a folder should post at, or None for 'now'."""
    m = NAME_RE.match(folder_name)
    if not m:
        return None
    y, mo, d, h, mi = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(h or 9), int(mi or 0), tzinfo=LONDON)
    except ValueError:
        raise PostError(f"The date/time at the start of the folder name '{folder_name}' "
                        "isn't a real date. Use the format 2026-10-06 0900.")


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "post"


# ---------- images ----------

def prepare_images(folder):
    files = sorted((p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS),
                   key=lambda p: p.name.lower())
    if not files:
        raise PostError("No images found. Add JPG, PNG or WEBP images to the folder.")
    if len(files) > 10:
        raise PostError(f"Found {len(files)} images. Instagram allows at most 10 per post.")

    out_dir = MEDIA / slug(folder.name)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    outputs = []
    for i, src in enumerate(files, start=1):
        try:
            img = ImageOps.exif_transpose(Image.open(src))
        except Exception:
            raise PostError(f"'{src.name}' couldn't be opened as an image. Re-export it as a JPG.")
        ratio = img.width / img.height
        if ratio < 0.8 - 0.01 or ratio > 1.91 + 0.01:
            raise PostError(
                f"'{src.name}' is {img.width}x{img.height}. Instagram only accepts shapes between "
                "portrait 4:5 (e.g. 1080x1350) and landscape 1.91:1 (e.g. 1080x566). "
                "Square 1080x1080 is always fine. Please resize it and try again.")
        if img.mode != "RGB":
            bg = Image.new("RGB", img.size, "white")
            rgba = img.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[3])
            img = bg
        if img.width > 1440:
            img = img.resize((1440, round(1440 / ratio)), Image.LANCZOS)
        dest = out_dir / f"{i:02d}.jpg"
        img.save(dest, "JPEG", quality=92, optimize=True)
        outputs.append(dest)
    return outputs


def publish_images(paths, label):
    """Commit the JPGs so they have a public URL, and return those URLs."""
    git("add", *[str(p.relative_to(ROOT)) for p in paths])
    git("commit", "-m", f"Prepare images for Instagram post: {label}")
    git("push")
    sha = git("rev-parse", "HEAD") or "DRYRUN"
    repo = os.getenv("GITHUB_REPOSITORY", "geneticrebalance/geneticrebalance-ig-poster")
    urls = [f"https://raw.githubusercontent.com/{repo}/{sha}/{p.relative_to(ROOT).as_posix()}"
            for p in paths]
    if not DRY_RUN:
        for u in urls:  # make sure the images are reachable before handing them to Instagram
            for _ in range(10):
                if requests.head(u, timeout=20).status_code == 200:
                    break
                time.sleep(3)
            else:
                raise PostError("The images couldn't be reached at a public link. "
                                "Check the GitHub project is set to Public.")
    return urls


# ---------- Instagram ----------

def ig(method, path, **params):
    if DRY_RUN:
        log(f"[dry run] {method} {path} {sorted(k for k in params if k != 'access_token')}")
        return {"id": "DRY", "status_code": "FINISHED", "permalink": "https://instagram.com/p/dry"}
    r = requests.request(method, f"{GRAPH}/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    data = r.json()
    if r.status_code != 200:
        err = data.get("error", {})
        msg = err.get("error_user_msg") or err.get("message") or str(data)
        code = err.get("code")
        if code == 190:
            msg = ("The Instagram access token has expired or is invalid. Generate a new one in the "
                   "Meta developer dashboard and update the IG_ACCESS_TOKEN secret in GitHub.")
        elif code == 100 and err.get("error_subcode") == 33:
            msg = ("Instagram says the account ID doesn't match the token. Check the IG_ACCOUNT_ID "
                   "secret is the number shown next to 'geneticrebalance' when generating the token.")
        raise PostError(f"Instagram error: {msg} (code {code}, subcode {err.get('error_subcode')})")
    return data


def wait_ready(container_id, token):
    for _ in range(30):
        status = ig("GET", container_id, fields="status_code", access_token=token).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise PostError(f"Instagram couldn't process an image (status {status}). "
                            "Try re-exporting the image as a standard JPG.")
        time.sleep(4)
    raise PostError("Instagram took too long to process the images. Upload the folder into 'posts' again to retry.")


def post_to_instagram(urls, caption, token, account_id):
    if len(urls) == 1:
        cid = ig("POST", f"{account_id}/media", image_url=urls[0], caption=caption,
                 access_token=token)["id"]
    else:
        children = []
        for i, u in enumerate(urls, 1):
            log(f"  Uploading slide {i}/{len(urls)}...")
            child = ig("POST", f"{account_id}/media", image_url=u, is_carousel_item="true",
                       access_token=token)["id"]
            wait_ready(child, token)
            children.append(child)
        cid = ig("POST", f"{account_id}/media", media_type="CAROUSEL",
                 children=",".join(children), caption=caption, access_token=token)["id"]
    wait_ready(cid, token)
    media_id = ig("POST", f"{account_id}/media_publish", creation_id=cid,
                  access_token=token)["id"]
    link = ig("GET", media_id, fields="permalink", access_token=token).get("permalink", "")
    return media_id, link


# ---------- main ----------

def move(folder, dest_root, note_name, note):
    dest_root.mkdir(exist_ok=True)
    dest = dest_root / folder.name
    if dest.exists():
        dest = dest_root / f"{folder.name} ({datetime.now(LONDON):%Y-%m-%d %H%M%S})"
    shutil.move(str(folder), str(dest))
    (dest / note_name).write_text(note, encoding="utf-8")
    git("add", "-A", "posts", dest_root.name)
    git("commit", "-m", f"{dest_root.name.capitalize()}: {folder.name}")
    git("push")


def main():
    token = os.getenv("IG_ACCESS_TOKEN", "")
    account_id = os.getenv("IG_ACCOUNT_ID", "")
    if not DRY_RUN and (not token or not account_id):
        sys.exit("IG_ACCESS_TOKEN and IG_ACCOUNT_ID secrets must be set in GitHub.")

    now = datetime.now(LONDON)
    POSTS.mkdir(exist_ok=True)
    folders = sorted(p for p in POSTS.iterdir()
                     if p.is_dir() and not p.name.lower().startswith(("draft", "_", ".")))
    failures = 0

    for folder in folders:
        try:
            when = due_time(folder.name)
            if when and when > now:
                log(f"Waiting: '{folder.name}' is scheduled for {when:%a %d %b %H:%M}")
                continue
            log(f"Posting: '{folder.name}'")
            caption_files = sorted(folder.glob("*.txt"))
            caption = caption_files[0].read_text(encoding="utf-8-sig").strip() if caption_files else ""
            if len(caption) > 2200:
                raise PostError(f"The caption is {len(caption)} characters. Instagram's limit is 2,200.")
            if caption.count("#") > 30:
                raise PostError("The caption has more than 30 hashtags. Instagram's limit is 30.")
            images = prepare_images(folder)
            urls = publish_images(images, folder.name)
            media_id, link = post_to_instagram(urls, caption, token, account_id)
            log(f"  Posted! {link}")
            move(folder, POSTED, "result.txt",
                 f"Posted on {datetime.now(LONDON):%d %b %Y at %H:%M}\n{link}\nMedia ID: {media_id}\n")
        except PostError as e:
            failures += 1
            log(f"  FAILED: {e}")
            move(folder, FAILED, "error.txt",
                 f"This post was NOT published.\n\n{e}\n\n"
                 "To try again: fix the problem and upload the corrected folder into 'posts' again.\n")

    if failures:
        sys.exit(f"{failures} post(s) failed - see the error.txt in the 'failed' folder.")
    log("Done.")


if __name__ == "__main__":
    main()
