# -*- coding: utf-8 -*-
"""采集 davidwuw0811 的 awesome-gpt-image2-prompts 单页站。

数据就是站点同目录的 prompts.json,自带中文标题(title_cn)。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch_json, log, save_snapshot  # noqa: E402

SITE = "https://davidwuw0811-boop.github.io/awesome-gpt-image2-prompts/"
SOURCE = {
    "id": "david",
    "name": "Awesome GPT-Image-2 Prompts (davidwuw0811)",
    "url": SITE,
}


def main() -> int:
    data = fetch_json(f"{SITE}prompts.json")
    items = []
    for p in data:
        prompt = (p.get("prompt") or "").strip()
        if not prompt:
            continue
        image = p.get("image")
        items.append(
            {
                "title": (p.get("title_en") or p.get("title_cn") or "").strip(),
                "titleZh": (p.get("title_cn") or "").strip() or None,
                "prompt": prompt,
                "rawCategory": p.get("category_cn") or p.get("category"),
                "tags": [],
                "author": p.get("author"),
                "image": f"{SITE}{image}" if image else None,
                "images": [],
                "needsReference": bool(p.get("needs_ref")),
                "sourceUrl": SITE,
                "createdAt": None,
                "stats": {},
                "note": p.get("note"),
            }
        )
    log(f"[david] 采集 {len(items)} 条(源站 {len(data)} 条)")
    save_snapshot("david", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
