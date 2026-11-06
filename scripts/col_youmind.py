# -*- coding: utf-8 -*-
"""采集 YouMind-OpenLab/awesome-gpt-image-2(CC BY 4.0)。

数据内嵌在 README_zh.md,条目结构:
### No. N: [分类前缀 - ]标题
  #### 📖 描述 / #### 📝 提示词(代码块)/ #### 🖼️ 生成图片(<img>)/ #### 📌 详情
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import fetch, log, save_snapshot  # noqa: E402

REPO = "YouMind-OpenLab/awesome-gpt-image-2"
SOURCE = {
    "id": "youmind",
    "name": "YouMind Awesome GPT-Image-2",
    "url": "https://github.com/YouMind-OpenLab/awesome-gpt-image-2",
    "license": "CC BY 4.0",
}

ENTRY_RE = re.compile(r"^### No\. \d+:\s*(.+)$", re.M)
SECTION_RE = re.compile(r"^#### ", re.M)
IMG_RE = re.compile(r"<img[^>]+src=\"(https?://[^\"]+)\"")
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
DATE_RE = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")


def _sections(body: str) -> dict[str, str]:
    """把条目正文按 '#### ' 小标题切分成 {标题: 内容}。"""
    marks = [(m.start(), m.group(0)) for m in SECTION_RE.finditer(body)]
    out: dict[str, str] = {}
    for idx, (start, mark) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(body)
        head = body[start + len(mark) : body.find("\n", start)].strip()
        out[head] = body[body.find("\n", start) + 1 : end].strip()
    return out


def _parse_date(text: str) -> str | None:
    m = DATE_RE.search(text or "")
    if not m:
        return None
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def main() -> int:
    md = fetch(
        f"https://raw.githubusercontent.com/{REPO}/main/README_zh.md"
    ).decode("utf-8", errors="replace")

    matches = list(ENTRY_RE.finditer(md))
    items = []
    seen_spans: list[tuple[int, int]] = []
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md)
        title_line = m.group(1).strip()
        # 条目可能重复出现(精选区 + 全量区),靠 prompt 去重即可,这里跳过已解析标题
        heading_span = (m.start(), end)
        if any(a <= m.start() < b for a, b in seen_spans):
            continue
        seen_spans.append(heading_span)

        body = md[start:end]
        sections = _sections(body)

        prompt = ""
        code = re.search(r"```[a-zA-Z]*\n(.*?)```", sections.get("📝 提示词", ""), re.S)
        if code:
            prompt = code.group(1).strip()
        if not prompt:
            continue

        # 分类 = 标题里 " - " 前的前缀(如 "个人资料 / 头像 - xxx")
        raw_category = None
        title = title_line
        if " - " in title_line:
            prefix, rest = title_line.split(" - ", 1)
            raw_category, title = prefix.strip(), rest.strip()

        # 图片:🖼️ 生成图片 区块里的 <img src>
        imgs = IMG_RE.findall(sections.get("🖼️ 生成图片", "") or body)

        # 详情:作者/来源/时间/语言
        detail = sections.get("📌 详情", "")
        author, source_url = None, None
        for name, url in LINK_RE.findall(detail):
            if author is None and ("x.com" in url or "twitter.com" in url) and "status" not in url:
                author = name
            if source_url is None and ("status" in url or "Twitter" in name or "X " in name):
                source_url = url
        if source_url is None:
            for _, url in LINK_RE.findall(detail):
                if "x.com" in url or "twitter.com" in url:
                    source_url = url
                    break
        lang_m = re.search(r"多语言[:：]\s*(\w+)", detail)
        lang = (lang_m.group(1) if lang_m else "").lower() or None

        desc = re.sub(r"\s+", " ", sections.get("📖 描述", "")).strip()

        items.append(
            {
                "title": title or desc[:40],
                "prompt": prompt,
                "rawCategory": raw_category,
                "tags": [desc[:30]] if desc else [],
                "author": author,
                "image": imgs[0] if imgs else None,
                "images": imgs,
                "needsReference": False,
                "sourceUrl": source_url or SOURCE["url"],
                "createdAt": _parse_date(detail),
                "lang": lang,
                "stats": {},
            }
        )

    log(f"[youmind] 从 README 解析 {len(items)} 条")
    save_snapshot("youmind", {"source": SOURCE, "items": items})
    if items:
        cats = sorted({str(i["rawCategory"]) for i in items if i["rawCategory"]})
        log(f"[youmind] 原生分类前缀({len(cats)}): {cats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
