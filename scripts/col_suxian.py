# -*- coding: utf-8 -*-
"""采集水仙的AI提示词画廊(prompt.qqsrc.com)。

数据布局:meta.json(分类体系)+ list.part1-3.json(轻量)+ prompts.part1-3.json(全文)。
图片 CDN:https://r2.qqsrc.com/<image>
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch_json, log, save_snapshot  # noqa: E402

SITE = "https://prompt.qqsrc.com/"
IMG_BASE = "https://r2.qqsrc.com/"
SOURCE = {
    "id": "suxian",
    "name": "水仙的AI提示词",
    "url": SITE,
    "note": "仅供学习交流,版权归原作者;如需移除请联系源站",
}

LIST_PARTS = [f"{SITE}data/list.part{i}.json" for i in (1, 2, 3)]
FULL_PARTS = [f"{SITE}data/prompts.part{i}.json" for i in (1, 2, 3)]


def fetch_parts(urls: list[str]) -> list[dict]:
    """并行语义上逐个抓取,单分片失败降级为空(照搬源站容错)。"""
    out: list[dict] = []
    for url in urls:
        try:
            data = fetch_json(url)
            if isinstance(data, list):
                out.extend(data)
        except Exception as err:  # noqa: BLE001
            log(f"  [suxian] 分片失败跳过 {url}: {err}")
    return out


def main() -> int:
    # 分类体系:子分类 → 大分类(meta.json 的 majors[].subs[].name)
    sub_to_major: dict[str, str] = {}
    try:
        meta = fetch_json(f"{SITE}data/meta.json")
        for major in meta.get("majors") or []:
            for sub in major.get("subs") or []:
                sub_to_major[sub.get("name", "")] = major.get("name", "")
    except Exception as err:  # noqa: BLE001
        log(f"  [suxian] meta.json 加载失败(仅影响大分类): {err}")

    full = fetch_parts(FULL_PARTS)
    by_id = {str(p.get("id")): p for p in full if p.get("id") is not None}
    light = fetch_parts(LIST_PARTS)
    for p in light:  # 补全 full 分片可能缺的条目(无正文的仅元数据)
        pid = str(p.get("id"))
        if pid not in by_id:
            by_id[pid] = p

    items = []
    for pid, p in by_id.items():
        prompt = (p.get("prompt") or "").strip()
        title = (p.get("title") or "").strip()
        if not prompt and not title:
            continue
        sub_cat = (p.get("category") or "").strip()
        major = sub_to_major.get(sub_cat, "")
        raw_category = sub_cat or major
        tags = [t for t in (major, sub_cat) if t and t != raw_category]
        tags += [t for t in (p.get("themes") or []) if t] + [t for t in (p.get("styles") or []) if t]
        image = p.get("image") or p.get("thumb")
        items.append(
            {
                "title": title,
                "prompt": prompt,
                "rawCategory": raw_category or None,
                "tags": list(dict.fromkeys(t for t in tags if t)),
                "author": None,
                "image": f"{IMG_BASE}{image}" if image else None,
                "images": [
                    f"{IMG_BASE}{im}" for im in (p.get("images") or []) if im
                ],
                "needsReference": False,
                "sourceUrl": f"{SITE}detail.html?id={pid}",
                "createdAt": None,
                "stats": {"likes": p.get("likes") or 0},
                "tweet": p.get("tweet"),
            }
        )
    log(f"[suxian] 采集 {len(items)} 条(源站总索引 {len(by_id)} 条)")
    save_snapshot("suxian", {"source": SOURCE, "items": items})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
