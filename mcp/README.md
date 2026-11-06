# 提示词库 MCP Server

把聚合提示词库作为 MCP 工具暴露给 AI 客户端。纯 Python 标准库实现,**零依赖、零部署**,
本地 stdio 运行。

## 工具列表

| 工具 | 说明 |
|---|---|
| `search_prompts(query, category?, source?, limit?, deep?)` | 关键词检索(标题/中文标题/分类);0 命中自动降级全文;`deep=true` 强制全文 |
| `get_prompt(id)` | 取一条完整提示词(正文/效果图/出处) |
| `list_categories()` | 分类、来源与计数 |
| `random_pick(category?, n?)` | 随机推荐(找灵感) |
| `stats()` | 库存统计 |
| `contribute_template()` | 返回投稿 JSON schema(数据飞轮) |

## 数据源(二选一)

- `--repo <owner/name>`(或环境变量 `PG_REPO`):读 raw.githubusercontent.com,适合仓库已推送后
- `--data-dir <仓库根目录>`(或 `PG_DATA_DIR`):直接读本地克隆;都不传时默认用本脚本所在仓库

缓存:内存 + `.cache/mcp/` 文件缓存,TTL 30 分钟(改数据后可删缓存目录)。

## 客户端接入

### ZCode(`.zcode/mcp.json` 或全局配置)

```json
{
  "mcpServers": {
    "prompt-gallery": {
      "command": "python",
      "args": ["D:/UGit/prompt-gallery/mcp/server.py", "--repo", "你的用户名/仓库名"]
    }
  }
}
```

### Claude Desktop(`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "prompt-gallery": {
      "command": "python",
      "args": ["D:/UGit/prompt-gallery/mcp/server.py", "--repo", "你的用户名/仓库名"]
    }
  }
}
```

> 本地开发期(还没推 GitHub)把 `--repo` 换成 `--data-dir "D:/UGit/prompt-gallery"` 即可。

### 手动测试

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_prompts","arguments":{"query":"手办","limit":3}}}' \
  | python mcp/server.py
```
