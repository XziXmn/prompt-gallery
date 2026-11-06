# -*- coding: utf-8 -*-
"""采集 X 热门提示词 feed(xianyu110/awesome-gptimage2 每小时自动更新)。

latest-prompts.json:LLM 从 X 抓取的 GPT Image 2 热门帖,含互动数据。
免费获得"X 实时通道",无需任何 API key。数据可信度取决于上游,卡片保留原推链接供核查。
"""
from __future__ import annotations

import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch_json, log, save_snapshot  # noqa: E402


def _check_images(urls: list[str]) -> set[str]:
    """并发探测图链,返回不可达集合(twimg 删除/过期常见)。"""
    def ok(u: str) -> str | None:
        try:
            req = urllib.request.Request(u, method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0 (compatible; gallery-check/1.0)")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return None if resp.status == 200 else u
        except Exception:  # noqa: BLE001
            return u

    bad: set[str] = set()
    with ThreadPoolExecutor(max_workers=12) as ex:
        for r in ex.map(ok, set(urls)):
            if r:
                bad.add(r)
    return bad

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
    dropped_noimg = 0
    for it in raw_items:
        prompt = (it.get("prompt") or "").strip()
        text = (it.get("text") or "").strip()
        if not prompt or len(prompt) < 20:
            continue
        # 必须带效果图:无图的推文多是教程/公告而非提示词案例,全部丢弃
        images = [u for u in (it.get("image_urls") or []) if u]
        primary = it.get("primary_image_url") or (images[0] if images else None)
        if not primary:
            dropped_noimg += 1
            continue
        stats = {
            "likes": int(it.get("like_count") or 0),
            "views": int(it.get("view_count") or 0),
            "retweets": int(it.get("retweet_count") or 0),
        }
        title = text[:40].strip() or prompt[:40].strip()
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
    # 校验推文图链可达(twimg 删除/过期即 404),坏图整条丢弃
    bad = _check_images([i["image"] for i in items])
    if bad:
        items = [i for i in items if i["image"] not in bad]
    log(f"[xtrend] 采集 {len(items)} 条(丢弃无图 {dropped_noimg}、坏图 {len(bad)};feed 生成于 {data.get('meta', {}).get('generated_at_utc')})")
    save_snapshot("xtrend", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
