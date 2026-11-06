# -*- coding: utf-8 -*-
"""汉化辅助:生成待翻译清单 / 合并翻译结果。

用法:
  python scripts/translate_queue.py --make [--limit 100]  生成 data/translate-queue.json
  python scripts/translate_queue.py --merge               合并 inbox 里的翻译(实际由 col_inbox 完成,此命令仅提示)

配合 grok-translate-prompt.txt 使用:把队列粘给 Grok bot,把返回的 JSON 存进 data/inbox/。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, log  # noqa: E402

QUEUE_PATH = DATA_DIR / "translate-queue.json"
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def make(limit: int) -> int:
    payload = json.loads((DATA_DIR / "prompts.json").read_text(encoding="utf-8"))
    pending = []
    for it in payload["items"]:
        # 没有中文标题,且原标题本身不是中文(已是中文则无需翻译)
        if it.get("titleZh"):
            continue
        title = it.get("title") or ""
        if not title or CJK_RE.search(title):
            continue
        pending.append({"id": it["id"], "title": title[:120]})
        if len(pending) >= limit:
            break
    QUEUE_PATH.write_text(
        json.dumps({"type": "translate-queue", "count": len(pending), "items": pending}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    log(f"[translate] 待翻译 {len(pending)} 条 → {QUEUE_PATH}")
    log("[translate] 下一步:打开 grok-translate-prompt.txt,按说明把队列交给 Grok bot,")
    log("[translate] 把返回 JSON 存到 data/inbox/translations-YYYYMMDD.json,然后重跑 pipeline 即可。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", action="store_true", help="生成待翻译队列")
    parser.add_argument("--merge", action="store_true", help="合并翻译(实际由 col_inbox.py 完成)")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.merge:
        log("[translate] 翻译合并由 scripts/col_inbox.py 在每次 pipeline 中自动完成(扫描 data/inbox/)。")
        return 0
    return make(args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
