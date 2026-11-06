# -*- coding: utf-8 -*-
"""采集 freestylefly/awesome-gpt-image-2(苍何画廊 ①号站后端)。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch_json, log, save_snapshot  # noqa: E402

REPO = "freestylefly/awesome-gpt-image-2"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main/data"
SOURCE = {
    "id": "canghe",
    "name": "苍何 GPT-Image2 Gallery",
    "url": "https://gpt-image2.canghe.ai/",
    "repo": f"https://github.com/{REPO}",
}


def main() -> int:
    data = fetch_json(f"{RAW_BASE}/cases.json")
    cases = data.get("cases") or []
    items = []
    for c in cases:
        prompt = (c.get("prompt") or "").strip()
        if not prompt:
            continue
        image = c.get("image")
        image_url = f"{RAW_BASE}{image}" if image else None
        items.append(
            {
                "title": (c.get("title") or c.get("imageAlt") or "").strip(),
                "prompt": prompt,
                "rawCategory": c.get("category"),
                "tags": [s for s in (c.get("styles") or []) if s]
                + [s for s in (c.get("scenes") or []) if s],
                "author": c.get("sourceLabel"),
                "image": image_url,
                "images": [],
                "needsReference": bool(c.get("needsRef")),
                "sourceUrl": c.get("sourceUrl") or c.get("githubUrl") or SOURCE["url"],
                "createdAt": None,
                "stats": {},
                "featured": bool(c.get("featured")),
            }
        )
    log(f"[canghe] 采集 {len(items)} 条(源站 {data.get('totalCases')} 条)")
    save_snapshot("canghe", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
