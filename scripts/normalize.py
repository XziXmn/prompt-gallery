# -*- coding: utf-8 -*-
"""归一化:合并各源快照 → 赋 id → 跨源去重 → 自动分类 → 应用翻译 → data/prompts.json。

id = 源前缀 + 规范化prompt的SHA1前12位;跨源重复时保留字段更全的条目。
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, SOURCES_DIR, dedup_key, detect_lang, engagement, log  # noqa: E402
from taxonomy import OTHER, UNIFIED_CATEGORIES, classify, normalize_sub  # noqa: E402

OUT_PATH = DATA_DIR / "prompts.json"
TRANSLATIONS_PATH = SOURCES_DIR / "translations.json"
AUTO_TRANSLATIONS_PATH = SOURCES_DIR / "translations-auto.json"
DIMS_PATH = SOURCES_DIR / "img-dims.json"
TRANSLATION_FILES = {"translations.json", "translations-auto.json", "inbox-ledger.json", "img-dims.json"}

# 去重冲突时的源优先级(越小越优先保留)
SOURCE_PRIORITY = ["canghe", "handbook", "david", "youmind", "gptimage2", "suxian", "xtrend", "inbox"]


def _richness(item: dict) -> int:
    """条目信息丰富度评分,去重时保留分高者。"""
    score = 0
    if item.get("image"):
        score += 100
    if item.get("title"):
        score += 20
    if item.get("titleZh"):
        score += 30
    score += min(len(item.get("prompt") or "") // 200, 30)
    score += min(len(item.get("tags") or []), 8)
    score += min(int(engagement(item.get("stats"))), 50) // 10
    return score


def main() -> int:
    snapshots = sorted(SOURCES_DIR.glob("*.json")) if SOURCES_DIR.exists() else []
    snapshots = [p for p in snapshots if p.name not in TRANSLATION_FILES]

    # 翻译库:人工(Grok bot)+ 自动两条通道,合并为 {id: {titleZh, promptZh}}
    translations: dict[str, dict] = {}
    for tpath in (TRANSLATIONS_PATH, AUTO_TRANSLATIONS_PATH):
        if tpath.exists():
            for t in json.loads(tpath.read_text(encoding="utf-8")).get("items") or []:
                rec = translations.setdefault(t.get("id") or "", {})
                if t.get("titleZh"):
                    rec["titleZh"] = t["titleZh"]
                if t.get("promptZh"):
                    rec["promptZh"] = t["promptZh"]

    # 图片尺寸表 {urlHash: {w,h}}
    dims_map: dict[str, dict] = {}
    if DIMS_PATH.exists():
        dims_map = json.loads(DIMS_PATH.read_text(encoding="utf-8"))

    by_key: dict[str, dict] = {}
    per_source: dict[str, int] = {}
    dedup_hits: dict[str, int] = {}
    unmapped = 0
    kw_fallback = 0
    total_in = 0

    for snap in snapshots:
        source_id = snap.stem
        try:
            payload = json.loads(snap.read_text(encoding="utf-8"))
        except Exception as err:  # noqa: BLE001
            log(f"[normalize] 快照损坏跳过 {snap.name}: {err}")
            continue
        meta = payload.get("source") or {}
        count = 0
        for raw in payload.get("items") or []:
            total_in += 1
            prompt = (raw.get("prompt") or "").strip()
            if not prompt:
                continue
            title = (raw.get("title") or "").strip() or prompt[:40]
            if len(title) > 80:  # 个别源站把整段提示词存成标题,截断防撑爆版面
                title = title[:80].rstrip() + "…"
            t12 = translations.get(f"{source_id}-{dedup_key(prompt)}") or {}
            raw_cat = raw.get("rawCategory")

            # 图片宽高比(masonry 精确分列;img_dimensions.py 产出)
            ar = None
            image_url = raw.get("image")
            if image_url and DIMS_PATH.exists():
                dims = dims_map.get(hashlib.sha1(image_url.encode()).hexdigest()[:12])
                if dims and dims.get("w") and dims.get("h"):
                    ar = round(dims["h"] / dims["w"], 3)

            item = {
                "id": f"{source_id}-{dedup_key(prompt)}",
                "title": title,
                "titleZh": (raw.get("titleZh") or t12.get("titleZh") or "")[:80] + ("…" if len(raw.get("titleZh") or t12.get("titleZh") or "") > 80 else "") or None,
                "promptZh": raw.get("promptZh") or t12.get("promptZh"),
                # 源站原生子分类(卡片左上角彩色标签用)
                "sub": normalize_sub(raw_cat),
                "prompt": prompt,
                "category": None,
                "tags": list(dict.fromkeys(
                    (normalize_sub(t) or t) for t in (raw.get("tags") or []) if t
                ))[:10],
                "source": {
                    "id": source_id,
                    "name": meta.get("name") or source_id,
                    "url": raw.get("sourceUrl") or meta.get("url"),
                },
                "author": raw.get("author"),
                "image": raw.get("image"),
                "images": (raw.get("images") or [])[:6],
                "needsReference": bool(raw.get("needsReference")),
                "createdAt": raw.get("createdAt"),
                "lang": raw.get("lang") or detect_lang(prompt),
                "stats": raw.get("stats") or {},
                "hot": engagement(raw.get("stats")),
                "ar": ar,
            }
            if raw.get("rawCategory") and raw.get("rawCategory") not in item["tags"]:
                item["tags"].append(str(normalize_sub(raw.get("rawCategory")))[:30])
            item["tags"] = item["tags"][:12]

            cat, rule = classify(source_id, raw.get("rawCategory"), title, prompt)
            item["category"] = cat
            if rule.startswith("kw"):
                kw_fallback += 1
            elif rule == "none":
                unmapped += 1
            if raw.get("featured"):
                item["featured"] = True

            key = dedup_key(prompt)
            if key in by_key:
                dedup_hits[source_id] = dedup_hits.get(source_id, 0) + 1
                old = by_key[key]
                pri_new = SOURCE_PRIORITY.index(source_id) if source_id in SOURCE_PRIORITY else 99
                pri_old = SOURCE_PRIORITY.index(old["source"]["id"]) if old["source"]["id"] in SOURCE_PRIORITY else 99
                keep_new = (
                    (pri_new, _richness(item)) < (pri_old, _richness(old))
                    if pri_new == pri_old
                    else pri_new < pri_old
                )
                if keep_new:
                    by_key[key] = item
            else:
                by_key[key] = item
            count += 1
        per_source[source_id] = count

    items = sorted(
        by_key.values(),
        key=lambda x: (x.get("createdAt") or "0", x.get("hot") or 0),
        reverse=True,
    )
    payload = {
        "meta": {
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total": len(items),
            "perSource": per_source,
            "dedupHits": dedup_hits,
            "categoryCounts": {
                c: sum(1 for i in items if i["category"] == c) for c in UNIFIED_CATEGORIES
            },
        },
        "items": items,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    log(f"[normalize] 输入 {total_in} 条 → 去重后 {len(items)} 条(重复合并 {sum(dedup_hits.values())} 条)")
    log(f"[normalize] 各源: {per_source}")
    log(f"[normalize] 关键词兜底 {kw_fallback} 条,完全未映射(归入其他) {unmapped} 条 "
        f"({unmapped * 100 // max(len(items), 1)}%)")
    log(f"[normalize] 分类分布: {payload['meta']['categoryCounts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
