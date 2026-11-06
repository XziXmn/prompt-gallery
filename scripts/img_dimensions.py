# -*- coding: utf-8 -*-
"""图片尺寸探测:只拉每张图的前 64KB,标准库解析宽高,产出 ar(高/宽)供 masonry 精确分列。

输出 data/sources/img-dims.json:{urlHash: {"w":..,"h":..}}
断点续传;并发 24 线程;单图失败静默跳过(masonry 回落默认比例)。
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import DATA_DIR, SOURCES_DIR, log  # noqa: E402

DIMS_PATH = SOURCES_DIR / "img-dims.json"
MAX_READ = 64 * 1024
UA = {"User-Agent": "Mozilla/5.0 (compatible; gallery-dims/1.0)"}


def image_size(data: bytes):
    """从图片头部字节解析 (w, h);不支持/不足返回 None。"""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8 " and len(data) >= 30:
            return (
                int.from_bytes(data[26:28], "little") & 0x3FFF,
                int.from_bytes(data[28:30], "little") & 0x3FFF,
            )
        if chunk == b"VP8L" and len(data) >= 26:
            b = data[21:26]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0x0F) << 10) | (b[2] << 2) | (b[1] >> 6))
            return w, h
        if chunk == b"VP8X" and len(data) >= 30:
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if data[:2] == b"\xff\xd8":  # JPEG:扫描 SOF0/1/2/3/5/6/7/9/10/14
        i = 2
        n = len(data)
        while i + 9 < n:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            if i + 4 > n:
                return None
            seglen = int.from_bytes(data[i + 2 : i + 4], "big")
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                if i + 9 <= n:
                    h = int.from_bytes(data[i + 5 : i + 7], "big")
                    w = int.from_bytes(data[i + 7 : i + 9], "big")
                    return w, h
                return None
            i += 2 + seglen
    return None


def fetch_head(url: str):
    req = urllib.request.Request(url, headers={**UA, "Range": "bytes=0-65535"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read(MAX_READ)


def main() -> int:
    payload = json.loads((DATA_DIR / "prompts.json").read_text(encoding="utf-8"))
    urls = []
    seen = set()
    for it in payload["items"]:
        u = it.get("image")
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    store = {}
    if DIMS_PATH.exists():
        store = json.loads(DIMS_PATH.read_text(encoding="utf-8"))
    todo = [u for u in urls if hashlib.sha1(u.encode()).hexdigest()[:12] not in store]
    log(f"[dims] 唯一图片 {len(urls)} · 已测 {len(store)} · 本轮待测 {len(todo)}")
    if not todo:
        return 0

    lock = threading.Lock()
    done = [0]
    ok = [0]

    def work(url: str):
        key = hashlib.sha1(url.encode()).hexdigest()[:12]
        try:
            w, h = image_size(fetch_head(url))
            if w and h and w > 8 and h > 8:
                with lock:
                    store[key] = {"w": w, "h": h}
                    ok[0] += 1
        except Exception:  # noqa: BLE001 — 单图失败不影响整体
            pass
        finally:
            with lock:
                done[0] += 1
                if done[0] % 200 == 0:
                    DIMS_PATH.parent.mkdir(parents=True, exist_ok=True)
                    tmp = DIMS_PATH.with_suffix(".tmp")
                    tmp.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
                    tmp.replace(DIMS_PATH)
                    log(f"[dims] 进度 {done[0]}/{len(todo)}(成功 {ok[0]})")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=24) as ex:
        list(ex.map(work, todo))

    DIMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIMS_PATH.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")
    log(f"[dims] 完成:成功 {ok[0]}/{len(todo)},耗时 {time.time() - t0:.0f}s → {DIMS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
