#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_PICGO_SERVER = "http://127.0.0.1:36677/upload"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def upload_to_picgo(image_path: Path, server: str) -> str:
    if not image_path.is_file():
        raise SystemExit(f"Image not found: {image_path}")
    if image_path.stat().st_size == 0:
        raise SystemExit(f"Image is empty: {image_path}")

    payload = json.dumps({"list": [str(image_path.resolve())]}).encode("utf-8")
    request = urllib.request.Request(
        server,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise SystemExit(f"PicGo upload failed: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"PicGo returned non-JSON response: {raw[:200]}") from exc

    if not data.get("success"):
        raise SystemExit(f"PicGo upload failed: {raw[:500]}")

    result = data.get("result")
    if not isinstance(result, list) or not result or not isinstance(result[0], str):
        raise SystemExit(f"PicGo response missing result[0]: {raw[:500]}")

    return result[0]


def split_frontmatter(text: str) -> tuple[list[str], str]:
    if not text.startswith("---\n"):
        return [], text

    end = text.find("\n---\n", 4)
    if end == -1:
        return [], text

    frontmatter_text = text[4:end]
    body = text[end + len("\n---\n") :]
    return frontmatter_text.splitlines(), body


def upsert_frontmatter_field(lines: list[str], key: str, value: str) -> list[str]:
    field = f"{key}: {yaml_quote(value)}"
    pattern = re.compile(rf"^{re.escape(key)}\s*:")

    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = field
            return lines

    insert_after_keys = ("cover_title", "title")
    for target_key in insert_after_keys:
        target = re.compile(rf"^{re.escape(target_key)}\s*:")
        for index, line in enumerate(lines):
            if target.match(line):
                lines.insert(index + 1, field)
                return lines

    lines.insert(0, field)
    return lines


def upsert_body_cover_preview(body: str, cover_url: str, alt: str, insert_preview: bool) -> str:
    body = body.lstrip("\n")

    h1_match = re.search(r"(?m)^#\s+.+$", body)
    h1_start = h1_match.start() if h1_match else 0
    before_h1 = body[:h1_start]
    after_h1 = body[h1_start:]

    existing_cover = re.compile(
        r"(?im)^!\[(?:公众号封面|cover image)[^\]]*\]\([^)]+\)\s*\n*"
    )

    if existing_cover.search(before_h1):
        before_h1 = existing_cover.sub("", before_h1)

    if insert_preview:
        preview = f"![{alt}]({cover_url})"
        if before_h1.strip():
            return before_h1.rstrip() + "\n\n" + preview + "\n\n" + after_h1.lstrip("\n")
        return preview + "\n\n" + after_h1.lstrip("\n")

    if not before_h1.strip():
        return after_h1.lstrip("\n")

    return before_h1.rstrip() + "\n\n" + after_h1.lstrip("\n")


def update_article(article_path: Path, cover_url: str, alt: str, field: str, insert_preview: bool) -> bool:
    old_text = article_path.read_text(encoding="utf-8")
    frontmatter_lines, body = split_frontmatter(old_text)

    if frontmatter_lines:
        frontmatter_lines = upsert_frontmatter_field(frontmatter_lines, field, cover_url)
        new_body = upsert_body_cover_preview(body, cover_url, alt, insert_preview)
        new_text = "---\n" + "\n".join(frontmatter_lines).rstrip() + "\n---\n\n" + new_body
    else:
        new_body = upsert_body_cover_preview(body, cover_url, alt, insert_preview)
        new_text = f"---\n{field}: {yaml_quote(cover_url)}\n---\n\n{new_body}"

    if old_text == new_text:
        return False

    article_path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upload a generated WeChat cover image to PicGo/OSS and write it to article frontmatter."
    )
    parser.add_argument("article", type=Path, help="Markdown article path")
    parser.add_argument("--image", type=Path, required=True, help="Local generated cover image")
    parser.add_argument("--server", default=os.environ.get("PICGO_SERVER", DEFAULT_PICGO_SERVER))
    parser.add_argument("--field", default="cover_image", help="Frontmatter field to update")
    parser.add_argument("--alt", default="公众号封面", help="Alt text for the H1-before cover preview inserted into the Markdown document")
    parser.add_argument("--no-body-preview", action="store_true", help="Do not insert a cover preview image above the H1")
    parser.add_argument("--delete-local", action="store_true", help="Delete local image after successful attach")
    args = parser.parse_args()

    article_path = args.article.resolve()
    image_path = args.image.resolve()

    if not article_path.is_file():
        raise SystemExit(f"Article not found: {article_path}")

    cover_url = upload_to_picgo(image_path, args.server)
    insert_preview = not args.no_body_preview
    changed = update_article(article_path, cover_url, args.alt, args.field, insert_preview)

    deleted_local = False
    if args.delete_local:
        image_path.unlink()
        deleted_local = True

    print(json.dumps({
        "article": str(article_path),
        "cover_image": cover_url,
        "field": args.field,
        "bodyPreview": insert_preview,
        "changed": changed,
        "deletedLocal": deleted_local,
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
