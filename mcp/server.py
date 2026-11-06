# -*- coding: utf-8 -*-
"""提示词库 MCP Server(stdio,纯标准库,零部署)。

把聚合提示词库以 MCP 工具形式暴露给任意 AI 客户端(ZCode / Claude Desktop / Cursor 等):
  - search_prompts(query, category?, source?, limit?)  关键词检索(标题/中文标题/标签,可选全文)
  - get_prompt(id)                                     取单条完整提示词
  - list_categories()                                  分类与计数
  - random_pick(category?, n)                          随机推荐
  - stats()                                            库存统计
  - contribute_template()                              返回投稿 schema(数据飞轮)

数据源二选一:
  --data-dir <path>   直接读本地克隆的 data/ 目录(开发模式)
  --repo <o/r>        读 raw.githubusercontent.com(默认;可用环境变量 PG_REPO)
缓存:内存 + .cache/mcp/ 文件缓存,TTL 默认 1800 秒。

协议:JSON-RPC 2.0 over stdio(newline-delimited),MCP tools 能力。
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "prompt-gallery-mcp", "version": "1.0.0"}
CACHE_TTL = 1800
ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / ".cache" / "mcp"

# ---------------------------------------------------------------- 数据访问
class Store:
    def __init__(self, data_dir: str | None, repo: str | None):
        # data_dir 语义:仓库根目录(其下含 data/);缺省用本脚本所在仓库
        self.data_dir = Path(data_dir).resolve() if data_dir else ROOT
        self.repo = repo
        self._mem: dict[str, tuple[float, object]] = {}

    def _base(self, rel: str) -> str:
        if not self.repo:
            return str(self.data_dir / rel)
        return f"https://raw.githubusercontent.com/{self.repo}/main/{rel}"

    def _load(self, rel: str, force_remote: bool = False):
        key = self._base(rel)
        now = time.time()
        hit = self._mem.get(key)
        if hit and now - hit[0] < CACHE_TTL:
            return hit[1]
        cache_file = CACHE_DIR / (re.sub(r"[^\w.-]", "_", rel) or "root")
        if not force_remote and cache_file.exists() and now - cache_file.stat().st_mtime < CACHE_TTL:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            self._mem[key] = (now, data)
            return data
        if self.data_dir:
            data = json.loads(Path(key).read_text(encoding="utf-8"))
        else:
            req = urllib.request.Request(key, headers={"User-Agent": "prompt-gallery-mcp/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self._mem[key] = (now, data)
        return data

    # -- 工具数据 --
    def index_lite(self) -> list:
        return self._load("data/prompts.index.lite.json")

    def index_full(self) -> list:
        return self._load("data/prompts.index.json")

    def stats(self) -> dict:
        return self._load("data/stats.json")

    def featured(self) -> list:
        return self._load("data/featured.json")

    def category_slice(self, category: str) -> list:
        data = self._load(f"data/prompts.by-category/{category}.json")
        return data.get("items") or []

    def ensure_full(self) -> dict:
        stats = self.stats()
        out: dict[str, dict] = {}
        for i in range(1, int(stats.get("fullParts") or 1) + 1):
            part = self._load(f"data/prompts.full.part{i}.json")
            for it in part.get("items") or []:
                out[it["id"]] = it
        return out


# ---------------------------------------------------------------- 工具实现
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _compact(it: dict) -> dict:
    """兼容全量条目(title/category)与 index 精简条目(t/c/s)两种形状。"""
    src = it.get("source")
    source = src.get("name") if isinstance(src, dict) else it.get("s")
    return {
        "id": it["id"],
        "title": it.get("titleZh") or it.get("title") or it.get("tz") or it.get("t"),
        "category": it.get("category") or it.get("c"),
        "source": source,
        "image": it.get("image") or it.get("img"),
        "needsReference": bool(it.get("needsReference") or it.get("nr")),
    }


def tool_search(store: Store, args: dict) -> dict:
    query = str(args.get("query") or "").strip()
    category = args.get("category")
    source = args.get("source")
    limit = min(int(args.get("limit") or 8), 30)
    deep = bool(args.get("deep", False))

    index = store.index_lite()
    q = query.lower()
    terms = [t for t in re.split(r"[\s,，]+", q) if t]

    pool = index
    if category:
        pool = [e for e in pool if e.get("c") == category]
    if source:
        pool = [e for e in pool if e.get("s") == source]

    def score(e: dict) -> int:
        if not terms:
            return 1
        hay = f"{e.get('t') or ''} {e.get('tz') or ''} {e.get('c') or ''}".lower()
        s = 0
        for t in terms:
            if t in (e.get("tz") or "").lower():
                s += 6
            if t in (e.get("t") or "").lower():
                s += 4
            if t in (e.get("c") or "").lower():
                s += 3
            if t in hay:
                s += 2
        return s

    scored = [(score(e), e) for e in pool]
    scored = [(s, e) for s, e in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    results = [e for _, e in scored[:limit]]

    # 标题检索 0 命中且有关键词 → 自动降级全文检索(较慢,首次会拉全量分片,之后有缓存)
    if not results and terms and not deep:
        deep = True

    # deep 模式且关键词没命中足够结果 → 全文检索(较慢,首次会拉全量分片)
    if deep and len(results) < limit and terms:
        full = store.ensure_full()
        extra = []
        for it in full.values():
            pl = (it.get("prompt") or "").lower()
            if any(t in pl for t in terms):
                extra.append(it)
        extra.sort(key=lambda x: -int(x.get("hot") or 0))
        have = {e["id"] for e in results}
        for it in extra:
            if it["id"] in have:
                continue
            results.append(
                {"id": it["id"], "t": it.get("title"), "tz": it.get("titleZh"),
                 "c": it.get("category"), "s": (it.get("source") or {}).get("id")}
            )
            if len(results) >= limit:
                break

    return {
        "totalIndexed": len(index),
        "matched": len(results),
        "items": results,
        "hint": "用 get_prompt(id) 获取完整提示词;传 deep=true 可全文检索",
    }


def tool_get(store: Store, args: dict) -> dict:
    pid = str(args.get("id") or "")
    full = store.ensure_full()
    it = full.get(pid)
    if not it:
        raise KeyError(f"未找到条目 {pid}(数据可能已更新,请重新检索)")
    out = dict(it)
    out["title_display"] = out.get("titleZh") or out.get("title")
    return out


def tool_categories(store: Store, _args: dict) -> dict:
    stats = store.stats()
    return {
        "total": stats.get("total"),
        "updatedAt": stats.get("generatedAt"),
        "categories": stats.get("categoryCounts"),
        "sources": stats.get("perSource"),
    }


def tool_random(store: Store, args: dict) -> dict:
    category = args.get("category")
    n = min(int(args.get("n") or 3), 10)
    if category:
        pool = store.category_slice(category)
    else:
        pool = store.index_full()
    picks = random.sample(pool, min(n, len(pool)))
    items = [_compact(e) for e in picks]
    return {"items": items, "hint": "用 get_prompt(id) 获取完整提示词"}


def tool_stats(store: Store, _args: dict) -> dict:
    return store.stats()


def tool_contribute(_store: Store, _args: dict) -> dict:
    return {
        "schema": {
            "type": "prompts",
            "items": [
                {
                    "title": "简短标题(中文优先)",
                    "titleZh": "中文标题(若原标题为英文)",
                    "prompt": "完整提示词原文,禁止翻译",
                    "category": "可选:海报排版/UI界面/电商产品/人像写真/摄影写实/插画艺术/3D潮玩/信息图表/Logo品牌/文字渲染/古风历史/游戏动漫/场景叙事/视频模板",
                    "tags": ["可选标签"],
                    "author": "@作者",
                    "image": "https://效果图URL",
                    "sourceUrl": "https://原帖链接",
                    "createdAt": "YYYY-MM-DD",
                    "needsReference": False,
                }
            ],
        },
        "howTo": "把 JSON 存为 data/inbox/xxx-YYYYMMDD.json 并提交到仓库(或网页上传),下次同步自动收编去重",
    }


TOOLS = [
    {
        "name": "search_prompts",
        "description": "在聚合提示词库中检索(标题/中文标题/分类;deep=true 时全文)。返回候选列表,再用 get_prompt 取全文。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "关键词,支持中英文,空格分隔多词"},
                "category": {"type": "string", "description": "限定统一分类,见 list_categories"},
                "source": {"type": "string", "description": "限定来源 id(canghe/suxian/david/handbook/xtrend/youmind/gptimage2/inbox)"},
                "limit": {"type": "integer", "description": "返回条数,默认 8,最大 30"},
                "deep": {"type": "boolean", "description": "全文检索(较慢),默认 false"},
            },
        },
    },
    {
        "name": "get_prompt",
        "description": "按 id 取一条完整提示词(含正文/图片/来源链接)。",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "list_categories",
        "description": "列出全部分类、来源与计数。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "random_pick",
        "description": "随机推荐几条提示词(可限定分类),用于灵感激发。",
        "inputSchema": {
            "type": "object",
            "properties": {"category": {"type": "string"}, "n": {"type": "integer"}},
        },
    },
    {
        "name": "stats",
        "description": "提示词库整体统计(总数/图片数/更新时间/去重情况)。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "contribute_template",
        "description": "获取向本库投稿新提示词的 JSON schema 与步骤。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def dispatch(store: Store, name: str, args: dict) -> dict:
    if name == "search_prompts":
        return tool_search(store, args)
    if name == "get_prompt":
        return tool_get(store, args)
    if name == "list_categories":
        return tool_categories(store, args)
    if name == "random_pick":
        return tool_random(store, args)
    if name == "stats":
        return tool_stats(store, args)
    if name == "contribute_template":
        return tool_contribute(store, args)
    raise KeyError(f"未知工具 {name}")


# ---------------------------------------------------------------- JSON-RPC over stdio
def write_msg(msg: dict) -> None:
    # 直接写二进制,避免 Windows 文本模式把 \n 翻译成 \r\n(stdio 协议要求 \n 分隔)
    data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="提示词库 MCP server")
    parser.add_argument("--data-dir", default=os.environ.get("PG_DATA_DIR"))
    parser.add_argument("--repo", default=os.environ.get("PG_REPO"))
    parser.add_argument("--http-timeout", type=int, default=60)
    args = parser.parse_args()
    store = Store(args.data_dir, args.repo)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            write_msg({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        method = msg.get("method") or ""
        mid = msg.get("id")
        is_resp_needed = mid is not None

        if method == "initialize":
            write_msg({
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "protocolVersion": (msg.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            })
        elif method == "notifications/initialized":
            pass  # 通知,不应答
        elif method == "ping":
            if is_resp_needed:
                write_msg({"jsonrpc": "2.0", "id": mid, "result": {}})
        elif method == "tools/list":
            write_msg({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name") or ""
            targs = params.get("arguments") or {}
            try:
                data = dispatch(store, name, targs)
                write_msg({
                    "jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]},
                })
            except KeyError as err:
                write_msg({
                    "jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": f"错误: {err}"}], "isError": True},
                })
            except Exception as err:  # noqa: BLE001
                write_msg({
                    "jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": f"数据加载失败: {err}"}], "isError": True},
                })
        elif is_resp_needed:
            write_msg({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}})
    return 0


if __name__ == "__main__":
    # Windows 默认 GBK,MCP stdio 协议为 UTF-8,三个流统一强制
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    raise SystemExit(main())
