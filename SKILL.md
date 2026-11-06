---
name: gpt-image-2-prompt-library
description: 检索聚合的 GPT Image 2 提示词库(9500+ 条,15 分类,8 渠道)。当用户想找图像生成提示词、参考某种效果的做法、或要为 GPT Image / Nano Banana 类模型构思提示词时使用。支持关键词/分类/全文检索,可返回可复制的完整提示词与原始出处。
---

# GPT Image 2 提示词库检索

一个持续更新的聚合提示词库。本技能教你如何查询它。

## 何时使用

- 用户要"XX 效果的提示词"(如:海报、手办、儿童绘本、UI 复刻、电商图)
- 用户想参考某个爆款图的做法、找可复制的完整 prompt
- 用户要为 GPT Image 2 / Nano Banana / 即梦等图像模型写提示词,想先看同类案例

## 推荐路径(按环境选择)

### 路径 A:已接入本库 MCP server(最优先)

调用工具:
1. `list_categories` → 了解分类与库存
2. `search_prompts(query="用户需求关键词", category=可选, limit=8)` → 得到候选(id/标题/分类/来源)
3. `get_prompt(id)` → 逐条取完整提示词展示,保留 `source.url` 出处
4. 想要灵感 → `random_pick(category?, n)`

### 路径 B:只能联网(HTTP)

按 `AI.md` 的数据契约操作(同仓库根目录下的 AI.md,或
`https://raw.githubusercontent.com/<owner/repo>/main/AI.md`):

1. 拉 `data/stats.json` 看总量与 `fullParts` 分片数
2. 拉 `data/prompts.index.lite.json` 精简索引,按 `c`(分类)、`t`/`tz`(标题)筛选
3. 按候选分类拉 `data/prompts.by-category/{分类}.json` 取全文
4. 需要全文关键词检索时拉 `data/prompts.full.part{N}.json` 逐片匹配

## 输出规范

- 提示词正文**原样给出**,不翻译不润色(它是给图像模型的)
- 每条标注来源名称与 `source.url`
- 用户描述的是"想要的效果"时,先给 3~5 条最接近的,再按需补充
- 可以在原文基础上帮用户替换 `[占位符]` 或 `{argument}` 的默认值

## 注意

- 数据每 6 小时更新;条目 id 可能因内容合并而变化
- `xtrend` 来源为上游自动采集,建议核对原帖后再引用
