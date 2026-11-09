# -*- coding: utf-8 -*-
"""死图巡检:HEAD 探测各源快照里的图片链接,失效条目直接从快照剔除。

背景:X 推文图(twimg)会被删/过期,采集时可达、上线后死亡,前端只能显示占位卡。
本脚本作为 pipeline 的常规步骤,每轮同步时清掉新死的图;图片数少的源全量探测,
水仙等大源按 8% 抽样(死亡是少数事件,抽样足够)。

用法:python scripts/prune_dead_images.py [--all]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import SOURCES_DIR, log  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (compatible; gallery-prune/1.0)"}

SKIP_FILES = {
    "translations.json", "translations-auto.json",
    "ai-titles.json", "inbox-ledger.json", "img-dims.json",
}


def alive(url: str) -> bool:
    """HEAD 优先,失败回退 Range GET;两者都不通才算死图。

    部分 CDN 拒绝 HEAD(403/405),只认 200 会把活图误判成死图。
    """
    for method, headers in (("HEAD", UA), ("GET", {**UA, "Range": "bytes=0-0"})):
        try:
            req = urllib.request.Request(url, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status in (200, 206):
                    return True
        except Exception:  # noqa: BLE001
            continue
    return False


def prune_snapshot(path: Path, sample_ratio: float | None) -> tuple[int, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    if not items:
        return 0, 0

    # 只探测卡片展示的主图
    checks = [(idx, it.get("image")) for idx, it in enumerate(items) if it.get("image")]
    if sample_ratio and len(checks) > 400:
        import random

        checks = random.sample(checks, int(len(checks) * sample_ratio))

    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(lambda c: (c[0], alive(c[1])), checks))
    dead_idx = {idx for idx, ok in results if not ok}
    # 保险丝:死图率 >50% 说明是探测方法被 CDN 拒绝,不是真失效,整源跳过
    if checks and len(dead_idx) / len(checks) > 0.5:
        raise RuntimeError(f"死图率 {len(dead_idx)}/{len(checks)} 异常,疑似 CDN 拒绝探测,跳过该源")

    # 主图死了 → 整条剔除(没有可展示的封面)
    kept = [it for idx, it in enumerate(items) if idx not in dead_idx]
    removed = len(items) - len(kept)
    if removed:
        data["items"] = kept
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    return len(items), removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="全量探测(默认大源抽样 8%)")
    args = parser.parse_args()

    total_removed = 0
    for path in sorted(SOURCES_DIR.glob("*.json")):
        if path.name in SKIP_FILES:
            continue
        ratio = None if args.all or path.stem in ("xtrend", "inbox") else 0.08
        try:
            n, removed = prune_snapshot(path, ratio)
            total_removed += removed
            if removed:
                log(f"[prune] {path.stem}: 剔除死图条目 {removed}/{n}")
        except Exception as err:  # noqa: BLE001
            log(f"[prune] {path.stem} 跳过: {err}")
    log(f"[prune] 完成,共剔除 {total_removed} 条死图条目")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
