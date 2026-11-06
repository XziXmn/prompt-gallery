# -*- coding: utf-8 -*-
"""收编 data/inbox/ 下的人工投喂文件(Grok bot 采集结果 / 翻译结果)。

支持的文件格式:
  1. 提示词贡献: {"type":"prompts","items":[...]} 或直接 items 数组
  2. 翻译合并:   {"type":"translations","items":[{"id":"xx","titleZh":"..."}]}

内容按不可信数据处理:只做 schema 校验与字段清洗,坏文件拒绝并报告,
不影响其他源。已收编过的文件(内容哈希一致)自动跳过。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import INBOX_DIR, SOURCES_DIR, log, save_snapshot  # noqa: E402

SOURCE = {
    "id": "inbox",
    "name": "收件箱(人工投喂)",
    "url": "https://github.com/",
    "note": "用 grok-collect-prompt.txt / grok-translate-prompt.txt 采集后放入 data/inbox/",
}

URL_RE = re.compile(r"^https?://\S+$")
MAX_PROMPT_LEN = 20000
LEDGER_PATH = SOURCES_DIR / "inbox-ledger.json"
TRANSLATIONS_PATH = SOURCES_DIR / "translations.json"


def _file_hash(content: bytes) -> str:
    return hashlib.sha1(content).hexdigest()[:12]


def _clean_item(idx: int, raw: object, filename: str, errors: list[str]) -> dict | None:
    if not isinstance(raw, dict):
        errors.append(f"{filename}#{idx}: 不是对象")
        return None
    prompt = str(raw.get("prompt") or "").strip()
    if not prompt:
        errors.append(f"{filename}#{idx}: 缺少 prompt")
        return None
    if len(prompt) > MAX_PROMPT_LEN:
        errors.append(f"{filename}#{idx}: prompt 超长({len(prompt)} 字符),拒绝")
        return None

    def _urls(value) -> list[str]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []
        return [u.strip() for u in value if isinstance(u, str) and URL_RE.match(u.strip())]

    images = _urls(raw.get("images"))
    image = raw.get("image")
    image = str(image).strip() if image and URL_RE.match(str(image).strip()) else None
    if image and image not in images:
        images = [image] + images

    source_url = raw.get("sourceUrl") or raw.get("url")
    source_url = str(source_url).strip() if source_url and URL_RE.match(str(source_url).strip()) else None

    created = raw.get("createdAt") or raw.get("date")
    created = str(created).strip() if created else None

    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags = [str(t).strip()[:30] for t in tags if str(t).strip()][:10]

    return {
        "title": str(raw.get("title") or prompt[:40]).strip()[:120],
        "titleZh": (str(raw.get("titleZh")).strip() or None) if raw.get("titleZh") else None,
        "prompt": prompt,
        "rawCategory": (str(raw.get("category")).strip() or None) if raw.get("category") else None,
        "tags": tags,
        "author": (str(raw.get("author")).strip() or None) if raw.get("author") else None,
        "image": image or (images[0] if images else None),
        "images": images[:6],
        "needsReference": bool(raw.get("needsReference")),
        "sourceUrl": source_url,
        "createdAt": created,
        "stats": {},
    }


def main() -> int:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    ledger = {}
    if LEDGER_PATH.exists():
        ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    errors: list[str] = []
    prompt_items: list[dict] = []
    new_translations: list[dict] = []
    processed, skipped = 0, 0

    for path in sorted(INBOX_DIR.glob("*.json")):
        content = path.read_bytes()
        fhash = _file_hash(content)
        if ledger.get(path.name) == fhash:
            skipped += 1
            continue
        try:
            data = json.loads(content.decode("utf-8", errors="replace"))
        except Exception as err:  # noqa: BLE001
            errors.append(f"{path.name}: JSON 解析失败({err})")
            continue

        if isinstance(data, dict) and data.get("type") == "translations":
            batch = data.get("items") or []
            ok = 0
            for t in batch if isinstance(batch, list) else []:
                tid = str(t.get("id") or "").strip()
                tzh = str(t.get("titleZh") or "").strip()
                if tid and tzh and len(tzh) <= 60:
                    new_translations.append({"id": tid, "titleZh": tzh, "fromFile": path.name})
                    ok += 1
                else:
                    errors.append(f"{path.name}: 翻译条目缺少 id/titleZh 或超长")
            if ok:
                ledger[path.name] = fhash
                processed += 1
                log(f"  [inbox] {path.name}: 收编翻译 {ok} 条")
        else:
            batch = data.get("items") if isinstance(data, dict) else data
            if not isinstance(batch, list):
                errors.append(f"{path.name}: 缺少 items 数组")
                continue
            ok = 0
            for idx, raw in enumerate(batch):
                item = _clean_item(idx, raw, path.name, errors)
                if item:
                    item["inboxFile"] = path.name
                    prompt_items.append(item)
                    ok += 1
            if ok:
                ledger[path.name] = fhash
                processed += 1
                log(f"  [inbox] {path.name}: 收编提示词 {ok} 条")

    # 写回 ledger 与累积翻译库
    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    existing_trans: dict[str, dict] = {}
    if TRANSLATIONS_PATH.exists():
        for t in json.loads(TRANSLATIONS_PATH.read_text(encoding="utf-8")).get("items") or []:
            existing_trans[t["id"]] = t
    for t in new_translations:
        existing_trans[t["id"]] = t
    TRANSLATIONS_PATH.write_text(
        json.dumps({"items": list(existing_trans.values())}, ensure_ascii=False), encoding="utf-8"
    )

    save_snapshot("inbox", {"source": SOURCE, "items": prompt_items})
    log(f"[inbox] 新收编文件 {processed} 个(跳过已收编 {skipped} 个),提示词 {len(prompt_items)} 条,翻译 {len(new_translations)} 条,累积翻译 {len(existing_trans)} 条")
    if errors:
        log(f"[inbox] 校验问题 {len(errors)} 条:")
        for e in errors[:20]:
            log(f"  - {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
