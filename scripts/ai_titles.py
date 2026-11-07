# -*- coding: utf-8 -*-
"""AI 标题生成与翻译(OpenAI 兼容接口,DeepSeek/中转均可)。

补齐免费翻译接口(gtx)做不了的三件事:
  1. 标题生成:标题缺失、或标题就是提示词开头(混同)的条目 → 生成中文短标题
  2. 标题翻译:有标题但无 titleZh 的条目 → 翻译
  3. 长提示词翻译:gtx 因超长跳过的 promptZh → 分段翻译

安全约定:API key 只放在本地环境变量,绝不写入仓库;提交到 git 的只有译文结果。

用法:
  export AI_API_KEY=sk-xxx                     # 必需
  export AI_BASE_URL=https://api.deepseek.com  # 可选,默认 DeepSeek
  export AI_MODEL=deepseek-chat                # 可选

  python scripts/ai_titles.py --dry-run   # 预览待处理量,不调用
  python scripts/ai_titles.py             # 全量处理,断点续传
  python scripts/ai_titles.py --limit 50  # 本轮最多 50 条

输出:data/sources/ai-titles.json,pipeline 的 normalize 自动合并。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, SOURCES_DIR, log, norm_text  # noqa: E402

OUT_PATH = SOURCES_DIR / "ai-titles.json"
PROMPTS_PATH = DATA_DIR / "prompts.json"
CJK = re.compile(r"[\u4e00-\u9fff]")

API_BASE = os.environ.get("AI_BASE_URL", "https://api.deepseek.com").rstrip("/")
API_KEY = os.environ.get("AI_API_KEY", "")
API_MODEL = os.environ.get("AI_MODEL", "deepseek-chat")


def load_store() -> dict:
    if OUT_PATH.exists():
        return {t["id"]: t for t in json.loads(OUT_PATH.read_text(encoding="utf-8")).get("items") or []}
    return {}


def save_store(store: dict) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"items": list(store.values())}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(OUT_PATH)


def chat(messages: list[dict], temperature: float = 0.3) -> str:
    import urllib.error

    body = json.dumps({"model": API_MODEL, "messages": messages, "temperature": temperature}).encode("utf-8")
    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                f"{API_BASE}/chat/completions", data=body, method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            if content:
                return content
            last_err = RuntimeError("空响应")
        except Exception as err:  # noqa: BLE001 — 网络与服务端 5xx 统一退避重试
            last_err = err
        time.sleep((5, 15, 45, 90)[min(attempt, 3)])
    raise RuntimeError(f"接口连续失败: {last_err}")


def parse_json_block(text: str):
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return []


def select_work(items: list[dict], store: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """返回 (需要生成标题, 需要翻译标题, 需要翻译长提示词)。"""
    need_gen, need_tz, need_pz = [], [], []
    for it in items:
        rec = store.get(it["id"]) or {}
        title = it.get("title") or ""
        prompt = it.get("prompt") or ""
        # 1) 标题生成:无标题 / 标题是提示词开头(混同)且偏长 / 标题过短无信息量
        mixed = bool(title) and bool(norm_text(prompt).startswith(norm_text(title)[:20]))
        need_title = (not title.strip()) or (mixed and len(title) > 25) or len(title.strip()) < 4
        if need_title and "title" not in rec:
            need_gen.append(it)
            continue  # 生成标题后顺带有中文标题,无需翻译
        # 2) 标题翻译:非中文标题且缺 titleZh
        if title and not it.get("titleZh") and not CJK.search(title) and "titleZh" not in rec:
            need_tz.append(it)
        # 3) 长提示词翻译:gtx 因超长跳过的且无 promptZh
        if prompt and not CJK.search(prompt) and not it.get("promptZh") and "promptZh" not in rec and len(prompt) > 3800:
            need_pz.append(it)
    return need_gen, need_tz, need_pz


GEN_SYSTEM = (
    "你是 AI 绘画提示词资料库的编辑。根据给出的图像生成提示词,提炼一个中文短标题:"
    "描述该提示词会生成什么画面,12 字以内,不加书名号和标点,不使用'一张/一幅'开头。"
    "只输出 JSON 数组,格式: [{\"id\":\"...\",\"title\":\"...\"}],不要输出其他文字。"
)

TZ_SYSTEM = (
    "你是翻译。把给出的图像提示词标题翻译成简体中文,12 字以内,保留核心意象。"
    "只输出 JSON 数组,格式: [{\"id\":\"...\",\"titleZh\":\"...\"}],不要输出其他文字。"
)

PZ_SYSTEM = (
    "你是翻译。把英文 AI 绘画提示词翻译成简体中文,保留 {argument} 占位符原样不译,"
    "专有名词可保留。直接输出译文,不要解释。"
)


def run_gen(batch: list[dict]) -> list[dict]:
    payload = [{"id": it["id"], "prompt": it["prompt"][:1500]} for it in batch]
    text = chat([
        {"role": "system", "content": GEN_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])
    return parse_json_block(text)


def run_tz(batch: list[dict]) -> list[dict]:
    payload = [{"id": it["id"], "title": it["title"][:120]} for it in batch]
    text = chat([
        {"role": "system", "content": TZ_SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ])
    return parse_json_block(text)


def run_pz(it: dict) -> str:
    return chat([
        {"role": "system", "content": PZ_SYSTEM},
        {"role": "user", "content": it["prompt"][:12000]},
    ], temperature=0.2).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=100000)
    parser.add_argument("--sleep", type=float, default=0.5)
    args = parser.parse_args()

    payload = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    store = load_store()
    need_gen, need_tz, need_pz = select_work(items, store)

    total_chars = sum(len(i["prompt"]) for i in need_pz) + sum(len(i["prompt"][:1500]) for i in need_gen)
    log(f"[ai] 待生成标题 {len(need_gen)} · 待翻译标题 {len(need_tz)} · 待翻译长提示词 {len(need_pz)}(约 {total_chars // 1000}k 字符)")
    log(f"[ai] 接口: {API_BASE} · 模型: {API_MODEL} · key: {'已配置' if API_KEY else '未配置!'}")
    if args.dry_run:
        for it in need_gen[:8]:
            log(f"  [gen] {it['id']} 现标题: {(it.get('title') or '(空)')[:40]}")
        log("[ai] dry-run 结束,未调用接口")
        return 0
    if not API_KEY:
        log("[ai] 错误:未配置 AI_API_KEY 环境变量")
        return 1

    ok = failed = 0
    todo_total = len(need_gen) + len(need_tz) + len(need_pz)
    done = 0

    def bump():
        nonlocal done
        done += 1
        if done % 10 == 0:
            save_store(store)
            log(f"[ai] 进度 {done}/{todo_total}(成功 {ok} 失败 {failed})")

    # 1) 批量生成标题(每批 10 条)
    for i in range(0, len(need_gen), 10):
        if ok >= args.limit:
            break
        batch = need_gen[i : i + 10]
        try:
            for r in run_gen(batch):
                rid = str(r.get("id") or "")
                t = str(r.get("title") or "").strip()
                if rid and t and len(t) <= 30:
                    rec = store.setdefault(rid, {"id": rid})
                    rec["title"] = t
                    rec["titleZh"] = t
                    ok += 1
            bump()
        except Exception as err:  # noqa: BLE001
            failed += 1
            log(f"    [ai] gen 批次失败: {err}")
        time.sleep(args.sleep)

    # 2) 批量翻译标题(每批 20 条)
    for i in range(0, len(need_tz), 20):
        if ok >= args.limit:
            break
        batch = need_tz[i : i + 20]
        try:
            for r in run_tz(batch):
                rid = str(r.get("id") or "")
                t = str(r.get("titleZh") or "").strip()
                if rid and t and len(t) <= 40:
                    rec = store.setdefault(rid, {"id": rid})
                    rec["titleZh"] = t
                    ok += 1
            bump()
        except Exception as err:  # noqa: BLE001
            failed += 1
            log(f"    [ai] tz 批次失败: {err}")
        time.sleep(args.sleep)

    # 3) 逐条翻译长提示词
    for it in need_pz:
        if ok >= args.limit:
            break
        try:
            zh = run_pz(it)
            if zh and len(zh) > 20:
                rec = store.setdefault(it["id"], {"id": it["id"]})
                rec["promptZh"] = zh
                ok += 1
            bump()
        except Exception as err:  # noqa: BLE001
            failed += 1
            log(f"    [ai] pz {it['id']} 失败: {err}")
        time.sleep(args.sleep)

    save_store(store)
    log(f"[ai] 本轮成功 {ok} · 失败 {failed} · 累计 {len(store)} 条 → {OUT_PATH}")
    log("[ai] 下一步:重跑 pipeline(normalize 自动合并),然后提交数据(key 不会进仓库)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
