# -*- coding: utf-8 -*-
"""采集 xianyu110/awesome-gptimage2 实战手册的社区案例与精选案例。

community-cases.json(740条,含 categoryZh)+ curated-cases.zh.json(25条)。
注意:其社区案例与 freestylefly 仓库高度重叠,normalize 阶段会跨源去重。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch_json, log, save_snapshot  # noqa: E402

REPO = "xianyu110/awesome-gptimage2"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/data"
SITE = "https://awesome.gptimage2.asia/"
SOURCE = {
    "id": "handbook",
    "name": "GPT-Image-2 提示词实战手册 (xianyu110)",
    "url": SITE,
    "repo": f"https://github.com/{REPO}",
}


def main() -> int:
    items = []

    community = fetch_json(f"{RAW}/community-cases.json")
    for c in community.get("cases") or []:
        prompt = (c.get("prompt") or "").strip()
        if not prompt:
            continue
        items.append(
            {
                "title": (c.get("title") or "").strip(),
                "titleZh": (c.get("title") or "").strip() or None,
                "prompt": prompt,
                "rawCategory": c.get("categoryZh") or c.get("category"),
                "tags": [s for s in (c.get("styles") or []) if s]
                + [s for s in (c.get("scenes") or []) if s],
                "author": c.get("sourceLabel"),
                "image": c.get("image"),
                "images": [],
                "needsReference": bool(c.get("needReferenceImages")),
                "sourceUrl": c.get("sourceUrl") or c.get("caseUrl") or SITE,
                "createdAt": None,
                "stats": {},
                "origin": c.get("source"),
            }
        )
    n_community = len(items)

    curated = fetch_json(f"{RAW}/curated-cases.zh.json")
    for c in curated.get("cases") or []:
        prompt = (c.get("promptText") or c.get("prompt") or "").strip()
        if not prompt:
            continue
        items.append(
            {
                "title": (c.get("title") or "").strip(),
                "titleZh": (c.get("title") or "").strip() or None,
                "prompt": prompt,
                "rawCategory": c.get("category"),
                "tags": [],
                "author": None,
                "image": c.get("image"),
                "images": [],
                "needsReference": False,
                "sourceUrl": SITE,
                "createdAt": None,
                "stats": {},
                "origin": c.get("source"),
            }
        )
    log(f"[handbook] 采集 {len(items)} 条(社区 {n_community} + 精选 {len(items) - n_community})")
    save_snapshot("handbook", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
