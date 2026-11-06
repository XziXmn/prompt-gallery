# 数据来源与致谢(ATTRIBUTION)

本仓库是一个聚合器:提示词内容均来自以下公开渠道,版权归原作者与原分享者所有,
仅供学习交流使用。若有侵权,请提交 issue,我们会立即移除对应内容或整源停用。

| 来源 ID | 名称 | 链接 | 说明 / 许可 |
|---|---|---|---|
| canghe | 苍何 GPT-Image2 Gallery | https://gpt-image2.canghe.ai/ | 数据取自其开源后端 [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) |
| suxian | 水仙的AI提示词 | https://prompt.qqsrc.com/ | 个人精选画廊;源站标注"仅供学习交流",图片仅热链不复制,可在 sources.json 一键停用 |
| david | Awesome GPT-Image-2 Prompts | https://davidwuw0811-boop.github.io/awesome-gpt-image2-prompts/ | 单页站;其数据汇总自 moosl、freestylefly、nexu-io 等开源仓库 |
| handbook | GPT-Image-2 提示词实战手册 | https://awesome.gptimage2.asia/ | 仓库 [xianyu110/awesome-gptimage2](https://github.com/xianyu110/awesome-gptimage2);整合 AI新榜、APPSO、甲木未来派等实测文章案例 |
| xtrend | X 热门提示词 | https://awesome.gptimage2.asia/ | 上游 [xianyu110/awesome-gptimage2](https://github.com/xianyu110/awesome-gptimage2) 的 GitHub Actions 每小时自动采集,本站仅镜像其 JSON |
| youmind | YouMind Awesome GPT-Image-2 | https://github.com/YouMind-OpenLab/awesome-gpt-image-2 | **CC BY 4.0**;提示词收集自社区,预览图托管于 youmind CDN |
| gptimage2 | awesome-gptimage2-prompts | https://github.com/gpt-image2/awesome-gptimage2-prompts | 社区聚合库(2717 条) |
| inbox | 收件箱(人工投喂) | — | Grok bot 采集 / 翻译结果,投喂者对内容负责 |

## 处理原则

1. **只存文字,不落图片**:所有效果图一律热链原始 CDN,不在本仓库复制分发图片文件。
2. **保留出处**:每条数据的 `source.url` 指回原始案例或原帖。
3. **跨源去重**:同一提示词多个来源收录时,保留来源优先级最高的一条(见 normalize.py 的 SOURCE_PRIORITY)。
4. **可一键停用**:编辑 `sources.json` 中对应源的 `"enabled": false` 即可整源移除。
5. 本仓库代码部分以 MIT 许可开源(见 LICENSE);数据部分按各来源许可提供。

## 特别致谢

感谢上述各站与仓库维护者、以及 X/Twitter 上乐于分享提示词的各位作者(@azed_ai、
@ZHO_ZHO_ZHO、@dotey 等)——本站只是把这些散落的公共财富整理得更容易找到。
