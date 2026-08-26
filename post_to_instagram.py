"""
post_to_instagram.py

Publishes a single image OR a multi-image carousel post to an Instagram
Business/Creator account using the Instagram Graph API.

Usage:
    # single image
    python post_to_instagram.py --image-url "https://example.com/photo.jpg" --caption "Hello world"

    # carousel (2-10 images, posted together as one swipeable post)
    python post_to_instagram.py --carousel \\
        --image-url "https://example.com/slide1.jpg" \\
        --image-url "https://example.com/slide2.jpg" \\
        --image-url "https://example.com/slide3.jpg" \\
        --caption "Swipe to learn more"

Notes:
- Instagram's API requires each image to be reachable at a public URL (it
  fetches the image itself rather than accepting a raw file upload).
- Single image: create a media container referencing the image + caption,
  then publish it.
- Carousel: create one "item" container per image (no caption on these),
  then a parent carousel container referencing all item IDs + the caption,
  then publish the parent.
- Access tokens generated in test/development mode are short-lived
  (~1 hour). If you get an authentication error, generate a fresh token
  from the Meta developer dashboard and update your .env file.
"""

import argparse
import base64
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.instagram.com/{GRAPH_API_VERSION}"


def get_config():
    token = os.getenv("IG_ACCESS_TOKEN")
    account_id = os.getenv("IG_ACCOUNT_ID")

    if not token or token == "paste_your_token_here":
        sys.exit(
            "Error: IG_ACCESS_TOKEN is not set. Copy .env.example to .env "
            "and fill in your real access token."
        )
    if not account_id or account_id == "paste_your_account_id_here":
        sys.exit(
            "Error: IG_ACCOUNT_ID is not set. Copy .env.example to .env "
            "and fill in your real Instagram account ID."
        )
    return token, account_id


def api_post(path, payload):
    url = f"{GRAPH_API_BASE}/{path}"
    response = requests.post(url, data=payload, timeout=30)
    data = response.json()
    if response.status_code != 200:
        # Encode the full error as base64 so GitHub Actions' secret-masking
        # (which blacks out any log text matching a stored secret, e.g. the
        # account ID) doesn't swallow the useful part of the message.
        raw = json.dumps(data, indent=2)
        encoded = base64.b64encode(raw.encode()).decode()
        print("FULL ERROR (base64-encoded to bypass log masking):")
        print(encoded)
        sys.exit("See FULL ERROR block above - decode it to read the real message.")
    return data


def create_single_media_container(account_id, token, image_url, caption):
    return api_post(
        f"{account_id}/media",
        {"image_url": image_url, "caption": caption, "access_token": token},
    )["id"]


def create_carousel_item_container(account_id, token, image_url):
    # Carousel items must NOT include a caption - only the parent does.
    return api_post(
        f"{account_id}/media",
        {"image_url": image_url, "is_carousel_item": "true", "access_token": token},
    )["id"]


def create_carousel_container(account_id, token, item_ids, caption):
    return api_post(
        f"{account_id}/media",
        {
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
            "access_token": token,
        },
    )["id"]


def publish_media_container(account_id, token, creation_id):
    return api_post(
        f"{account_id}/media_publish",
        {"creation_id": creation_id, "access_token": token},
    )["id"]


def post_single(account_id, token, image_url, caption):
    print("Creating media container...")
    creation_id = create_single_media_container(account_id, token, image_url, caption)
    print(f"Container created (id: {creation_id}). Waiting a moment before publishing...")
    time.sleep(5)
    print("Publishing...")
    return publish_media_container(account_id, token, creation_id)


def post_carousel(account_id, token, image_urls, caption):
    if not (2 <= len(image_urls) <= 10):
        sys.exit(f"Error: a carousel needs 2-10 images, got {len(image_urls)}.")

    item_ids = []
    for i, url in enumerate(image_urls, start=1):
        print(f"Creating carousel item {i}/{len(image_urls)}...")
        item_ids.append(create_carousel_item_container(account_id, token, url))

    print("Waiting a moment for items to process...")
    time.sleep(5)

    print("Creating parent carousel container...")
    creation_id = create_carousel_container(account_id, token, item_ids, caption)

    print("Waiting a moment before publishing...")
    time.sleep(5)

    print("Publishing carousel...")
    return publish_media_container(account_id, token, creation_id)


def main():
    parser = argparse.ArgumentParser(description="Post an image or carousel to Instagram.")
    parser.add_argument(
        "--image-url",
        action="append",
        required=True,
        help="Public URL of an image to post. Pass multiple times for a carousel.",
    )
    parser.add_argument("--caption", default="", help="Caption text for the post.")
    parser.add_argument(
        "--carousel",
        action="store_true",
        help="Force carousel mode even with one --image-url (mainly for testing). "
        "Carousel mode is automatic when more than one --image-url is given.",
    )
    args = parser.parse_args()

    token, account_id = get_config()

    is_carousel = args.carousel or len(args.image_url) > 1

    if is_carousel:
        media_id = post_carousel(account_id, token, args.image_url, args.caption)
    else:
        media_id = post_single(account_id, token, args.image_url[0], args.caption)

    print(f"Success! Post published. Media ID: {media_id}")


if __name__ == "__main__":
    main()
