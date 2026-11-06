# -*- coding: utf-8 -*-
"""生成首页精选 featured.json。

规则:有人工标记(featured)的优先,再按 互动分 + 有图 + 提示词长度适中 挑选,
分类尽量分散。可手工编辑 data/featured.json(数组 = 精选条目 id,顺序即轮播顺序)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, log  # noqa: E402

FEATURED_PATH = DATA_DIR / "featured.json"
TARGET = 12
MAX_PROMPT_LEN = 1800


def main() -> int:
    payload = json.loads((DATA_DIR / "prompts.json").read_text(encoding="utf-8"))
    items = payload["items"]

    if FEATURED_PATH.exists():  # 人工已维护 → 保留人工选择,仅校验 id 有效性
        manual = json.loads(FEATURED_PATH.read_text(encoding="utf-8"))
        valid = [fid for fid in manual if any(it["id"] == fid for it in items)]
        if len(valid) >= 6:
            FEATURED_PATH.write_text(json.dumps(valid, ensure_ascii=False, indent=1), encoding="utf-8")
            log(f"[featured] 保留人工精选 {len(valid)} 条")
            return 0

    candidates = [
        it
        for it in items
        if it.get("image") and MAX_PROMPT_LEN >= len(it.get("prompt") or "") >= 80
    ]
    # 标记精选优先,其余按互动分
    marked = [it for it in candidates if it.get("featured")]
    rest = sorted(
        [it for it in candidates if not it.get("featured")],
        key=lambda x: (x.get("hot", 0), x.get("createdAt") or ""),
        reverse=True,
    )
    pool = marked + rest

    picked: list[dict] = []
    used_cats: dict[str, int] = {}
    for it in pool:
        cat = it["category"]
        if used_cats.get(cat, 0) >= 2:  # 每类最多 2 条,保证轮播多样性
            continue
        picked.append(it)
        used_cats[cat] = used_cats.get(cat, 0) + 1
        if len(picked) >= TARGET:
            break

    FEATURED_PATH.write_text(
        json.dumps([it["id"] for it in picked], ensure_ascii=False, indent=1), encoding="utf-8"
    )
    cats = {}
    for it in picked:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    log(f"[featured] 自动精选 {len(picked)} 条,分类分布: {cats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
