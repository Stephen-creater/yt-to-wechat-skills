#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert SRT/VTT subtitles to a Markdown transcript.")
    parser.add_argument("input", type=Path, help="Path to .srt or .vtt subtitle file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Markdown output path")
    parser.add_argument("--source", default="待补", help="Original video/page URL")
    parser.add_argument("--title", default="", help="Original video title")
    parser.add_argument("--display-title", default="", help="Chinese readable Markdown title; defaults to output filename")
    parser.add_argument("--video-id", default="", help="Video ID")
    parser.add_argument("--language", default="", help="Subtitle language, e.g. en-orig")
    parser.add_argument("--subtitle-type", default="", help="manual or auto")
    parser.add_argument("--cover-url", default="", help="OSS URL for video cover/thumbnail image")
    parser.add_argument("--created", default=dt.date.today().isoformat(), help="Created date YYYY-MM-DD")
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_timestamp(value: str) -> str:
    value = value.strip().replace(",", ".")
    value = value.split()[0]
    parts = value.split(":")
    if len(parts) == 2:
        value = "00:" + value
    return value.split(".")[0]


def parse_subtitle(text: str) -> list[tuple[str, str]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[tuple[str, str]] = []

    for block in blocks:
        lines = [line.strip("\ufeff ") for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        if re.fullmatch(r"\d+", lines[0]):
            lines = lines[1:]
        time_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue

        start = clean_timestamp(lines[time_index].split("-->", 1)[0])
        body = clean_text(" ".join(lines[time_index + 1 :]))
        if body and (not cues or cues[-1][1] != body):
            cues.append((start, body))

    return cues


def yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_markdown(args: argparse.Namespace, cues: list[tuple[str, str]]) -> str:
    original_title = args.title or args.input.stem
    display_title = args.display_title or args.output.stem
    cover_url = getattr(args, "cover_url", "") or ""
    fm_lines = [
        "---",
        "type: 字幕",
        f"title: {yaml_string(display_title)}",
        f"source: {yaml_string(args.source)}",
        f"created: {yaml_string(args.created)}",
        "status: 未处理",
        f"original_title: {yaml_string(original_title)}",
        f"video_title: {yaml_string(original_title)}",
        f"video_id: {yaml_string(args.video_id)}",
        f"language: {yaml_string(args.language)}",
        f"subtitle_type: {yaml_string(args.subtitle_type)}",
        f"raw_subtitle: {yaml_string(str(args.input))}",
    ]
    if cover_url:
        fm_lines.append(f"cover: {yaml_string(cover_url)}")
    fm_lines.append("---")

    rows = [
        *fm_lines,
        "",
        f"# {display_title}",
        "",
    ]
    if cover_url:
        rows.append(f"![封面]({cover_url})")
        rows.append("")
    rows.extend([
        f"- 原始标题：{original_title}",
        f"- 来源：{args.source}",
        f"- 视频 ID：{args.video_id or '待补'}",
        f"- 字幕语言：{args.language or '待补'}",
        f"- 字幕类型：{args.subtitle_type or '待补'}",
        f"- 原始字幕：`{args.input}`",
        "",
        "## Transcript",
        "",
    ])
    rows.extend(f"[{timestamp}] {body}" for timestamp, body in cues)
    return "\n".join(rows).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    text = args.input.read_text(encoding="utf-8-sig")
    cues = parse_subtitle(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_markdown(args, cues), encoding="utf-8")
    print(f"wrote {args.output} ({len(cues)} cues)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
