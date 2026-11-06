# -*- coding: utf-8 -*-
"""数据校验:prompts.json 的完整性、唯一性、分类合法性与图片 URL 抽样探活。

pipeline 最后一步;任何 ERROR 级问题以非零码退出,阻止坏数据进入仓库。
"""
from __future__ import annotations

import json
import random
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, log  # noqa: E402
from taxonomy import UNIFIED_CATEGORIES  # noqa: E402

PROMPTS_PATH = DATA_DIR / "prompts.json"


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    payload = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    if not items:
        errors.append("prompts.json 为空")
        log("[validate] ERROR: 无数据")
        return 1

    ids = set()
    empty_prompt = 0
    bad_category = 0
    no_image = 0
    for it in items:
        if it["id"] in ids:
            errors.append(f"重复 id: {it['id']}")
        ids.add(it["id"])
        if not (it.get("prompt") or "").strip():
            empty_prompt += 1
        if it.get("category") not in UNIFIED_CATEGORIES:
            bad_category += 1
        if not it.get("image"):
            no_image += 1
    if empty_prompt:
        errors.append(f"{empty_prompt} 条 prompt 为空")
    if bad_category:
        errors.append(f"{bad_category} 条分类不在统一分类内")

    if len(items) < 1000:
        warnings.append(f"总条目偏少({len(items)}),检查采集器是否大面积失败")

    # 图片 URL 抽样探活(10 条,HEAD 探测超短超时,失败仅告警)
    with_images = [it for it in items if it.get("image")]
    sample = random.sample(with_images, min(8, len(with_images)))
    dead = 0
    for it in sample:
        try:
            req = urllib.request.Request(it["image"], method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0 (compatible; gallery-validate/1.0)")
            with urllib.request.urlopen(req, timeout=12):
                pass
        except Exception:  # noqa: BLE001
            dead += 1
    if dead:
        warnings.append(f"抽样图片 {dead}/{len(sample)} 条不可达(热链防盗链或网络抖动,卡片有占位兜底)")

    log(f"[validate] 共 {len(items)} 条 · 无图 {no_image} 条({no_image * 100 // len(items)}%) · 抽样图片不可达 {dead}")
    for w in warnings:
        log(f"[validate] WARN: {w}")
    for e in errors:
        log(f"[validate] ERROR: {e}")
    if errors:
        return 1
    log("[validate] 通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
