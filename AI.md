# AI.md — 机器可读的数据访问契约

本仓库是 GPT Image 2 提示词聚合库。所有数据为公开 JSON,任何能联网的 AI 可直接检索,
无需鉴权。本文档是给你(AI/Agent)的使用说明。

## 数据布局(raw.githubusercontent.com / 本地克隆均可)

```
data/
├── prompts.index.lite.json   # 精简索引 [{id, t(标题), tz(中文标题), c(分类), s(来源id)}]  最小,先拉这个
├── prompts.index.json        # 完整索引(含 img 图URL / nr 需参考图 / d 日期 / h 热度)
├── prompts.by-category/{分类}.json  # 按分类全量切片,15 个文件,条目为完整对象
├── prompts.full.part{1..N}.json     # 全量分片(数量见 stats.json 的 fullParts)
├── stats.json                # {total, images, perSource, categoryCounts, fullParts, generatedAt}
└── featured.json             # 首页精选条目 id 数组
```

基础 URL(把 `<owner/repo>` 换成实际仓库):

```
https://raw.githubusercontent.com/<owner/repo>/main/data/stats.json
```

## 条目完整 schema(by-category / full.part 中)

```json
{
  "id": "canghe-a3f9c2e1b8d4",
  "title": "原标题", "titleZh": "中文标题(可能缺省)",
  "prompt": "完整提示词原文 —— 供图像模型使用,不要翻译/改写",
  "promptZh": "提示词中文对照(机器翻译,仅供理解;可能缺省)",
  "category": "海报排版|UI界面|电商产品|人像写真|摄影写实|插画艺术|3D潮玩|信息图表|Logo品牌|文字渲染|古风历史|游戏动漫|场景叙事|视频模板|其他",
  "tags": ["来源原生分类", "风格词"],
  "source": {"id": "canghe", "name": "苍何 GPT-Image2 Gallery", "url": "原始案例链接"},
  "author": "@作者(可能缺省)", "image": "效果图URL", "images": ["多图"],
  "needsReference": false, "createdAt": "ISO日期(可能缺省)", "lang": "zh|en",
  "stats": {"likes": 0, "views": 0}, "hot": 123
}
```

## 查询配方

1. **按需求找提示词** → 拉 `prompts.index.lite.json`(约 1MB)本地筛选
   `c`(分类)/ `t`/`tz`(标题关键词)→ 按候选的 `c` 拉 `prompts.by-category/{分类}.json` 取全文。
2. **限定分类浏览** → 直接拉对应 `prompts.by-category/{分类}.json`。
3. **全文关键词** → 依次拉 `prompts.full.part{N}.json`(见 `stats.fullParts`),在 `prompt` 中匹配。
4. **要灵感** → 拉 `featured.json` + 对应 by-category 切片,或随机抽。

## 更便捷的方式:MCP server

如果环境支持 MCP,优先用本仓库自带的 stdio server(`mcp/server.py`,纯标准库零部署):

```
python mcp/server.py --repo <owner/repo>     # 远程模式
python mcp/server.py --data-dir /path/to/repo # 本地克隆模式
```

工具:`search_prompts` / `get_prompt` / `list_categories` / `random_pick` / `stats` / `contribute_template`

## 反向贡献(数据飞轮)

发现好的 GPT Image 2 提示词后,按 `contribute_template` 返回的 schema 组装 JSON,
存为 `data/inbox/<说明>-YYYYMMDD.json` 提交到仓库(或网页上传),下次自动同步即收编。
要求:`prompt` 必须是原文;效果图与原帖链接尽量提供;抄袭/私有内容勿投。

## 使用注意

- 提示词内容来自公开分享,转述时保留 `source.url` 出处;仅供学习交流。
- `xtrend` 来源由上游 LLM 自动采集,使用前可核对 `source.url` 原帖。
- 数据每 6 小时更新,id 在内容变更后可能变化;引用条目请以 `id` + `source.url` 双重定位。
