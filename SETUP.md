# SETUP — 从本地项目到线上站点

一次配置,之后全自动。预计 10 分钟。

## 第 1 步:推送到 GitHub

1. GitHub 上新建**公开**仓库(如 `prompt-gallery`),**不要**勾选任何初始化选项(README/.gitignore/license 都不要)。
2. 本地执行:

```bash
cd D:/UGit/prompt-gallery
git init -b main
git add .
git commit -m "init: 提示词聚合画廊"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

有 `gh` CLI 的话,1、2 两步可以合成:

```bash
cd D:/UGit/prompt-gallery
git init -b main && git add . && git commit -m "init: 提示词聚合画廊"
gh repo create prompt-gallery --public --source=. --push
```

## 第 2 步:开启 GitHub Pages

仓库 → **Settings** → **Pages** → **Build and deployment** → Source 选 **GitHub Actions**。

然后手动发一次:Actions → **Deploy Pages** → Run workflow。
之后每次 push(main 分支)或数据同步会自动重新发布。

站点地址:`https://<你的用户名>.github.io/<仓库名>/`

## 第 3 步:验证定时同步

Actions → **Sync Sources** → Run workflow。
跑完检查:仓库 `data/` 下出现 `prompts.json`、`prompts.index.json`、`prompts.by-category/` 等,
站点首页出现条目即成功。之后每 6 小时自动跑一次(只有数据有变化才会产生提交)。

> 注:schedule 触发只在默认分支有效;仓库 60 天无活动会被 GitHub 暂停定时任务,手动跑一次即恢复。

## 第 4 步:把 MCP 接入你的 AI 客户端

ZCode(`.zcode/mcp.json`)或 Claude Desktop(`claude_desktop_config.json`)加:

```json
{
  "mcpServers": {
    "prompt-gallery": {
      "command": "python",
      "args": ["D:/UGit/prompt-gallery/mcp/server.py", "--repo", "<你的用户名>/<仓库名>"]
    }
  }
}
```

重启客户端后,就可以直接问 AI:"帮我找适合儿童绘本的提示词",它会调用
`search_prompts` → `get_prompt` 返回可复制的原文和出处。

## 日常:用 Grok bot 投喂 X 热门提示词(可选)

1. 打开你的 Grok bot(已连接 X 账号),粘贴 `grok-collect-prompt.txt` 全文。
2. 它会输出一段 JSON;保存为 `data/inbox/x-20260506.json`(文件名随意,`.json` 结尾)。
3. push 到仓库(或 GitHub 网页端 Upload files 上传)。
4. 下次 Sync Sources 自动收编:校验 → 去重 → 分类 → 上线。

英文标题/提示词的中文翻译由 `scripts/translate_auto.py` 自动完成(免费翻译接口,
断点续传,Actions 与本地均可跑,pipeline 中已自动调用)。

## 可选:AI 标题生成与高质量翻译(DeepSeek 等)

无标题/标题混同的条目由 AI 生成中文短标题,超长英文提示词由 AI 补翻译。
**key 只放本地环境变量,绝不写入仓库;提交到 git 的只有译文结果**:

```bash
export AI_API_KEY=sk-xxx                        # DeepSeek 或任意 OpenAI 兼容中转
export AI_BASE_URL=https://api.deepseek.com     # 可选
export AI_MODEL=deepseek-chat                   # 可选

python scripts/ai_titles.py --dry-run   # 先预览待处理量
python scripts/ai_titles.py             # 全量(断点续传,可 --limit 分批)
python scripts/pipeline.py              # 重跑合并进正式数据
git add data && git commit -m "data: AI 标题/翻译" && git push
```

费用参考:全量一轮(168 标题 + 140 长文)约 100 万字符输入,DeepSeek 价格下约 ¥1-2。

## 常见问题

| 问题 | 处理 |
|---|---|
| 某个源不想采了 | `sources.json` 里改 `"enabled": false` |
| 网站图片挂了 | 个别 CDN 防盗链,卡片有占位兜底;若整源失效,停用该源 |
| 定时任务没跑 | Actions 页手动 Run workflow 一次即恢复 |
| 想改采集频率 | 改 `sync-sources.yml` 的 cron(注意上游 xtrend 每小时更新,6h 追赶足够) |
| MCP 报数据加载失败 | 删掉项目下 `.cache/` 目录重试(缓存 TTL 30 分钟) |
| 数据量会撑爆仓库吗 | 只存 JSON 且持续去重,Pages 上限 1GB,余量充足 |

## 可选:部署到自己的服务器(日本 VPS 等)

比 Pages 更快(国内直连)、图片走服务器本地缓存代理、不依赖 github.io。
一条命令启动,数据每 30 分钟自动从 GitHub 同步,详见 [deploy/README.md](deploy/README.md):

```bash
git clone https://github.com/<你的用户名>/<仓库名>.git && cd <仓库名>/deploy
docker compose up -d    # 站点 :8088 + 图片缓存代理 + 自动同步
```

GitHub Pages 可以保留作为免费备份入口,两者不冲突。
