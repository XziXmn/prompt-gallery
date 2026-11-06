# -*- coding: utf-8 -*-
"""公共工具:HTTP 抓取(重试/退避)、快照存取、规范化去重键、日志。

纯标准库实现,Windows / Linux(Actions)均可直接运行。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
INBOX_DIR = DATA_DIR / "inbox"

USER_AGENT = "Mozilla/5.0 (compatible; prompt-gallery-collector/1.0; +https://github.com)"


def log(msg: str) -> None:
    print(msg, flush=True)


def _setup_stdio() -> None:
    # Windows 控制台默认 GBK,强制 UTF-8 避免打印分类名时出错
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


_setup_stdio()


def fetch(
    url: str,
    *,
    timeout: int = 90,
    retries: int = 3,
    backoff: float = 4.0,
) -> bytes:
    """GET 一个 URL,指数退避重试,返回原始字节。"""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as err:  # noqa: BLE001 - 网络错误种类繁多,统一重试
            last_err = err
            if attempt < retries - 1:
                delay = backoff * (2**attempt)
                log(f"  [retry] {url} 第{attempt + 1}次失败:{err},{delay:.0f}s 后重试")
                time.sleep(delay)
    raise RuntimeError(f"抓取失败(已重试 {retries} 次):{url}") from last_err


def fetch_json(url: str) -> object:
    return json.loads(fetch(url).decode("utf-8", errors="replace"))


def save_snapshot(source_id: str, payload: object) -> Path:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    path = SOURCES_DIR / f"{source_id}.json"
    _write_json(path, payload)
    return path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(
    r"[\s\u3000-\u303f\uff00-\uffef!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~""''…—·]+"
)


def norm_text(text: str) -> str:
    """去重规范化:小写、去空白与中英文标点、NFKC 折叠。"""
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = _PUNCT_RE.sub("", text)
    return _WS_RE.sub("", text)


def dedup_key(prompt: str) -> str:
    return hashlib.sha1(norm_text(prompt).encode("utf-8")).hexdigest()[:12]


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def detect_lang(text: str) -> str:
    """粗略语言判断:中文字符占比高→zh,否则 en。"""
    text = text or ""
    if not text:
        return "en"
    cjk = len(_CJK_RE.findall(text))
    return "zh" if cjk >= max(2, int(len(text) * 0.06)) else "en"


def engagement(stats: dict) -> int:
    """互动分:点赞/浏览粗略加权,用于最热排序与精选补位。"""
    likes = int((stats or {}).get("likes") or 0)
    views = int((stats or {}).get("views") or 0)
    return likes * 10 + views


def read_sources_config() -> dict:
    cfg_path = ROOT / "sources.json"
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def load_source_config(source_id: str) -> dict:
    cfg = read_sources_config()
    entry = (cfg.get("sources") or {}).get(source_id) or {}
    entry.setdefault("enabled", True)
    return entry
