# -*- coding: utf-8 -*-
"""采集 gpt-image2/awesome-gptimage2-prompts(单文件 prompts.json,约 21.5MB)。

条目富字段:标题/描述/作者/点赞/发布时间/媒体列表/promptCategories,
部分条目带 translatedContent(中文翻译)。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch, log, save_snapshot  # noqa: E402

import json  # noqa: E402

REPO = "gpt-image2/awesome-gptimage2-prompts"
SOURCE = {
    "id": "gptimage2",
    "name": "awesome-gptimage2-prompts (gpt-image2 org)",
    "url": f"https://github.com/{REPO}",
}


def _pick_zh(translated) -> str | None:
    """translatedContent 可能是字符串或 {lang: text},尽量取中文。"""
    if not translated:
        return None
    if isinstance(translated, str):
        return translated.strip() or None
    if isinstance(translated, dict):
        for key in ("zh", "zh-CN", "zh-Hans", "Chinese", "zh_CN"):
            if translated.get(key):
                return str(translated[key]).strip() or None
        # 任意包含 CJK 的值
        import re

        for value in translated.values():
            if isinstance(value, str) and re.search(r"[\u4e00-\u9fff]", value):
                return value.strip()
    return None


def main() -> int:
    raw = fetch(f"https://raw.githubusercontent.com/{REPO}/main/prompts.json").decode(
        "utf-8", errors="replace"
    )
    data = json.loads(raw)
    entries = data.get("items") or (data if isinstance(data, list) else [])
    items = []
    for it in entries:
        prompt = (it.get("content") or "").strip()
        if not prompt:
            continue
        media = [m for m in (it.get("media") or []) if isinstance(m, str) and m]
        thumbs = [m for m in (it.get("mediaThumbnails") or []) if isinstance(m, str) and m]
        author = it.get("author") or {}
        cats = [c for c in (it.get("promptCategories") or []) if c]
        items.append(
            {
                "title": (it.get("title") or "").strip(),
                "titleZh": _pick_zh(it.get("translatedContent")),
                "description": (it.get("description") or "").strip() or None,
                "prompt": prompt,
                "rawCategory": (cats[0] if cats else None),
                "tags": cats[1:],
                "author": author.get("name"),
                "image": (thumbs[0] if thumbs else (media[0] if media else None)),
                "images": media,
                "needsReference": bool(it.get("needReferenceImages")),
                "sourceUrl": (it.get("sourceLink") or SOURCE["url"]).split("#")[0],
                "createdAt": it.get("sourcePublishedAt"),
                "stats": {"likes": int(it.get("likes") or 0)},
            }
        )
    log(f"[gptimage2] 采集 {len(items)} 条(源站 total={data.get('total')})")
    save_snapshot("gptimage2", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
