# -*- coding: utf-8 -*-
"""自动翻译:把英文标题/提示词批量译成中文,写入 data/sources/translations-auto.json。

- 断点续传:按 items.json 逐条处理,已译过的 id 跳过;每 10 条落盘一次
- 只做展示对照:prompt 原文永远保留,promptZh 仅用于阅读与站内搜索
- 长度/编码超限或反复失败的条目记录原因后跳过,不阻塞整体
- 可随时中断重跑;--limit 控制本轮最多处理多少条

用法:python scripts/translate_auto.py [--limit 500] [--sleep 0.35]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, SOURCES_DIR, log  # noqa: E402

CJK = re.compile(r"[\u4e00-\u9fff]")
AUTO_PATH = SOURCES_DIR / "translations-auto.json"
PROMPTS_PATH = DATA_DIR / "prompts.json"

MAX_Q_CHARS = 3800  # URL 编码前,单次请求的安全长度
GTX = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q="
BACKOFFS = [2, 6, 15, 40, 90]


def _store_load() -> dict[str, dict]:
    if AUTO_PATH.exists():
        data = json.loads(AUTO_PATH.read_text(encoding="utf-8"))
        return {t["id"]: t for t in data.get("items") or []}
    return {}


def _store_save(store: dict[str, dict]) -> None:
    AUTO_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = AUTO_PATH.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"items": list(store.values())}, ensure_ascii=False),
        encoding="utf-8",
    )
    tmp.replace(AUTO_PATH)


def gtx_translate(text: str, sleep: float) -> str:
    url = GTX + urllib.parse.quote(text)
    last_err = None
    for attempt, delay in enumerate([0] + BACKOFFS):
        if delay:
            log(f"    [translate] 失败重试 {attempt}/{len(BACKOFFS)},{delay}s 后…")
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            chunks = data[0] or []
            out = "".join(c[0] for c in chunks if c and c[0])
            if out.strip():
                return out.strip()
            last_err = RuntimeError("空结果")
        except Exception as err:  # noqa: BLE001
            last_err = err
    raise RuntimeError(f"翻译失败: {last_err}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--sleep", type=float, default=0.35, help="请求间隔(秒)")
    args = parser.parse_args()

    payload = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    store = _store_load()
    done_before = len(store)

    todo = []
    for it in items:
        need_title = it.get("title") and not it.get("titleZh") and not CJK.search(it["title"])
        need_prompt = not CJK.search(it.get("prompt", ""))
        rec = store.get(it["id"])
        need_title = need_title and not (rec and rec.get("titleZh"))
        need_prompt = need_prompt and not (rec and rec.get("promptZh"))
        if need_title or need_prompt:
            todo.append(it)
    log(f"[translate] 库存 {len(items)} · 已译 {done_before} · 本轮待译 {len(todo)} 条")
    if not todo:
        return 0

    ok, failed, skipped = 0, 0, 0
    since_save = 0
    for idx, it in enumerate(todo):
        if ok >= args.limit:
            log(f"[translate] 达到本轮上限 --limit {args.limit},已保存进度,重跑继续")
            break
        rec = store.get(it["id"]) or {"id": it["id"]}
        try:
            if "titleZh" not in rec and it.get("title") and not CJK.search(it["title"]):
                rec["titleZh"] = gtx_translate(it["title"][:300], args.sleep)
                time.sleep(args.sleep * random.uniform(0.7, 1.3))
            if "promptZh" not in rec and not CJK.search(it.get("prompt", "")):
                prompt = it["prompt"]
                if len(prompt) > MAX_Q_CHARS:
                    skipped += 1
                    rec["promptZh"] = None  # 超长不译,保留原文
                    rec["skipReason"] = f"过长 {len(prompt)} 字符"
                else:
                    rec["promptZh"] = gtx_translate(prompt, args.sleep)
                    time.sleep(args.sleep * random.uniform(0.7, 1.3))
            store[it["id"]] = rec
            ok += 1
            since_save += 1
            if since_save >= 10:
                _store_save(store)
                since_save = 0
                log(f"[translate] 进度 {ok}/{len(todo)}(累计 {len(store)})")
        except Exception as err:  # noqa: BLE001
            failed += 1
            log(f"    [translate] {it['id']}: {err}")
            if failed >= 8 and ok == 0:
                log("[translate] 连续失败且无成功,疑似网络受限,保存后退出(稍后重跑续传)")
                break
        if (idx + 1) % 1 == 0 and failed >= 20 and failed > ok * 0.5:
            log("[translate] 失败率过高,暂停本轮;已译进度已保存")
            break

    _store_save(store)
    zh_prompts = sum(1 for r in store.values() if r.get("promptZh"))
    zh_titles = sum(1 for r in store.values() if r.get("titleZh"))
    log(f"[translate] 本轮成功 {ok} · 失败 {failed} · 跳过长文 {skipped}")
    log(f"[translate] 累计:标题 {zh_titles} 条,提示词对照 {zh_prompts} 条 → {AUTO_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
