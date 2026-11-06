# 提示词画廊 · Prompt Gallery

多渠道自动聚合的 **GPT Image 2 提示词画廊**:网站浏览 + AI 可检索的提示词库,全程 GitHub 托管,
**零服务器、零部署、零 API 费用**。

![总数](https://img.shields.io/badge/提示词-9500+-6c8cff) ![来源](https://img.shields.io/badge/来源渠道-8-a06cff) ![分类](https://img.shields.io/badge/统一分类-15-4dd4ac)

## 它能做什么

| 能力 | 说明 |
|---|---|
| 🖼️ **画廊网站** | 首页精选轮播 + 瀑布流浏览 + 分类/来源筛选 + 全文搜索 + 一键复制 + 本地收藏(GitHub Pages) |
| 🤖 **AI 可查询** | 数据切片 + 文档契约([AI.md](AI.md) / [SKILL.md](SKILL.md)) + 本地 [MCP server](mcp/README.md),任何 AI 都能按需检索 |
| ⏱️ **自动更新** | GitHub Actions 每 6 小时从 8 个渠道同步 → 去重 → 自动分类 → 汉化 → 发布 |
| 🛡️ **零密钥** | 仓库不存任何 Secret;图片全部热链,仓库只存 JSON |
| 📥 **可投喂** | 用 Grok bot 采集 X 热门提示词,JSON 丢进 `data/inbox/` 自动收编(数据飞轮) |

## 数据来源(8 渠道)

[苍何 Gallery](https://gpt-image2.canghe.ai/) · [水仙的AI提示词](https://prompt.qqsrc.com/) ·
[davidwuw0811 单页站](https://davidwuw0811-boop.github.io/awesome-gpt-image2-prompts/) ·
[xianyu110 实战手册](https://awesome.gptimage2.asia/)(含其每小时更新的 **X 热门通道**) ·
[YouMind](https://github.com/YouMind-OpenLab/awesome-gpt-image-2)(CC BY 4.0) ·
[gpt-image2 org](https://github.com/gpt-image2/awesome-gptimage2-prompts) · 人工收件箱

详见 [ATTRIBUTION.md](ATTRIBUTION.md)(逐源署名、许可、一键停用)。

## 架构

```
8 个数据源(GitHub 仓库 / 公开 JSON)
        │  scripts/col_*.py(纯标准库采集器)
        ▼
data/sources/*.json 原始快照
        │  normalize.py(规范化 SHA1 去重 → 自动分类 → 应用汉化)
        ▼
data/prompts.json(全量)
        │  split_parts.py(索引 / 分类切片 / 全文分片 / 统计)
        ▼
┌─────────────────┬──────────────────┐
│  网站前端(原生 JS) │  AI 消费层          │
│  index/gallery/  │  AI.md + SKILL.md │
│  favorites/about │  mcp/server.py    │
└─────────────────┴──────────────────┘
        GitHub Actions:每 6h 同步 + push 即发 Pages
```

## 快速开始(本地)

```bash
# 全流程:采集 → 收编 → 归一化 → 精选 → 切片 → 校验
python scripts/pipeline.py

# 看网站
python -m http.server 8000    # 打开 http://127.0.0.1:8000

# 接入你的 AI 客户端(ZCode / Claude Desktop 等)
python mcp/server.py --data-dir .
```

依赖:仅 Python 3.10+(标准库),无 pip 安装。

## 日常操作

| 想做什么 | 怎么做 |
|---|---|
| 手动更新数据 | GitHub 仓库页 → Actions → "Sync Sources" → Run workflow |
| 停用某个源 | 编辑 `sources.json`,把对应 `"enabled"` 改为 `false` |
| 投喂 X 提示词 | 打开 `grok-collect-prompt.txt` 照做,JSON 存入 `data/inbox/` |
| 汉化更多标题 | `python scripts/translate_queue.py --make`,按 `grok-translate-prompt.txt` 翻译后放 `data/inbox/` |
| 调整首页精选 | 编辑 `data/featured.json`(条目 id 数组,顺序即轮播顺序) |
| 改采集频率 | 编辑 `.github/workflows/sync-sources.yml` 的 cron |

详细建仓与推送步骤见 [SETUP.md](SETUP.md)。

## 目录速览

```
scripts/    采集器 + 数据管道(纯 Python 标准库)
data/       数据(JSON):sources 原始快照 / prompts.* 切片 / inbox 收件箱
mcp/        本地 MCP server(零部署,接入 AI 客户端)
assets/     网站 CSS / JS(原生,无构建)
*.html      网站四页(首页/画廊/收藏/关于)
.github/    定时同步 + Pages 发布两个 workflow
```

## 许可

- 代码:MIT(见 [LICENSE](LICENSE))
- 提示词数据:按各来源许可提供,仅供学习交流(见 [ATTRIBUTION.md](ATTRIBUTION.md))
