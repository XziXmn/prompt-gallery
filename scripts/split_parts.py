# -*- coding: utf-8 -*-
"""切片:把 prompts.json 拆成站点与 AI 消费友好的多组文件。

输出:
  data/prompts.index.json           精简索引(站点首屏 / MCP 检索)
  data/prompts.by-category/{分类}.json   按分类全量切片(MCP/AI 按需取)
  data/prompts.full.part{N}.json    全量分片(站点后台懒加载全文搜索)
  data/stats.json                   统计(站点头部/关于页/MCP stats)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, log  # noqa: E402
from taxonomy import UNIFIED_CATEGORIES  # noqa: E402

PROMPTS_PATH = DATA_DIR / "prompts.json"
FULL_PART_SIZE = 1500  # 每分片条数


def main() -> int:
    payload = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    meta = payload["meta"]

    # 1) 精简索引(短字段名控制体积,约定见 AI.md)
    index = [
        {
            "id": it["id"],
            "t": it["title"],
            "tz": it.get("titleZh"),
            "c": it["category"],
            "s": it["source"]["id"],
            "img": it.get("image"),
            "nr": it.get("needsReference", False),
            "d": it.get("createdAt"),
            "h": it.get("hot", 0),
        }
        for it in items
    ]
    (DATA_DIR / "prompts.index.json").write_text(
        json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    # 2) 按分类切片
    cat_dir = DATA_DIR / "prompts.by-category"
    cat_dir.mkdir(parents=True, exist_ok=True)
    for old in cat_dir.glob("*.json"):
        old.unlink()
    for cat in UNIFIED_CATEGORIES:
        group = [it for it in items if it["category"] == cat]
        if not group:
            continue
        fname = f"{cat}.json"
        (cat_dir / fname).write_text(
            json.dumps({"category": cat, "count": len(group), "items": group}, ensure_ascii=False),
            encoding="utf-8",
        )

    # 3) 全量分片
    for i in range(0, (len(items) + FULL_PART_SIZE - 1) // FULL_PART_SIZE):
        chunk = items[i * FULL_PART_SIZE : (i + 1) * FULL_PART_SIZE]
        (DATA_DIR / f"prompts.full.part{i + 1}.json").write_text(
            json.dumps({"part": i + 1, "items": chunk}, ensure_ascii=False),
            encoding="utf-8",
        )
    n_parts = (len(items) + FULL_PART_SIZE - 1) // FULL_PART_SIZE
    # 清理旧分片(数量变少时)
    for old in DATA_DIR.glob("prompts.full.part*.json"):
        part_no = int(old.stem.replace("prompts.full.part", ""))
        if part_no > n_parts:
            old.unlink()

    # 4) 统计
    stats = {
        "generatedAt": meta["generatedAt"],
        "total": meta["total"],
        "images": sum(1 for it in items if it.get("image")),
        "needsReference": sum(1 for it in items if it.get("needsReference")),
        "perSource": meta["perSource"],
        "dedupHits": meta.get("dedupHits", {}),
        "categoryCounts": meta["categoryCounts"],
        "fullParts": n_parts,
    }
    (DATA_DIR / "stats.json").write_text(json.dumps(stats, ensure_ascii=False), encoding="utf-8")

    index_kb = (DATA_DIR / "prompts.index.json").stat().st_size // 1024
    log(f"[split] index {index_kb}KB · 分类切片 {len(list(cat_dir.glob('*.json')))} 个 · 全文分片 {n_parts} 个")

    # 5) 精简索引(无图片 URL,MCP / AI 检索用,体积约为完整索引的 1/5)
    lite = [
        {"id": it["id"], "t": it["title"], "tz": it.get("titleZh"), "c": it["category"], "s": it["source"]["id"]}
        for it in items
    ]
    (DATA_DIR / "prompts.index.lite.json").write_text(
        json.dumps(lite, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
