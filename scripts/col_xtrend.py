# -*- coding: utf-8 -*-
"""采集 X 热门提示词 feed(xianyu110/awesome-gptimage2 每小时自动更新)。

latest-prompts.json:LLM 从 X 抓取的 GPT Image 2 热门帖,含互动数据。
免费获得"X 实时通道",无需任何 API key。数据可信度取决于上游,卡片保留原推链接供核查。
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
    "id": "xtrend",
    "name": "X 热门提示词",
    "url": SITE,
    "repo": f"https://github.com/{REPO}",
    "note": "由 xianyu110 仓库的 GitHub Actions 每小时从 X 自动采集",
}


def main() -> int:
    data = fetch_json(f"{RAW}/latest-prompts.json")
    raw_items = data.get("items") or []
    if not raw_items:  # 兼容只有 dates 分组的情况
        raw_items = [i for d in (data.get("dates") or []) for i in (d.get("items") or [])]

    items = []
    for it in raw_items:
        prompt = (it.get("prompt") or "").strip()
        text = (it.get("text") or "").strip()
        if not prompt:
            continue
        stats = {
            "likes": int(it.get("like_count") or 0),
            "views": int(it.get("view_count") or 0),
            "retweets": int(it.get("retweet_count") or 0),
        }
        title = text[:40].strip() or prompt[:40].strip()
        images = [u for u in (it.get("image_urls") or []) if u]
        primary = it.get("primary_image_url") or (images[0] if images else None)
        items.append(
            {
                "title": title,
                "prompt": prompt,
                "rawCategory": None,
                "tags": [],
                "author": it.get("author"),
                "image": primary,
                "images": images,
                "needsReference": False,
                "sourceUrl": it.get("x_url") or it.get("url") or SOURCE["url"],
                "createdAt": it.get("created_at"),
                "stats": stats,
            }
        )
    log(f"[xtrend] 采集 {len(items)} 条(feed 生成于 {data.get('meta', {}).get('generated_at_utc')})")
    save_snapshot("xtrend", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
