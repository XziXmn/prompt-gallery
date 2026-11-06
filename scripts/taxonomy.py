# -*- coding: utf-8 -*-
"""两级自动分类规则引擎。

第一级:源站原生分类 → 统一分类的映射表(SOURCE_MAP)。
第二级:标题+提示词关键词规则(KEYWORD_RULES),用于没有分类的源。
均未命中 → "其他",原分类保留进 tags。
"""
from __future__ import annotations

import re

OTHER = "其他"

# 统一分类(顺序即网站展示顺序)
UNIFIED_CATEGORIES = [
    "海报排版",
    "UI界面",
    "电商产品",
    "人像写真",
    "摄影写实",
    "插画艺术",
    "3D潮玩",
    "信息图表",
    "Logo品牌",
    "文字渲染",
    "古风历史",
    "游戏动漫",
    "场景叙事",
    "视频模板",
    OTHER,
]

# ---------- 第一级:原生分类映射 ----------
# key 为 source id,value 为 {原生分类小写: 统一分类}
SOURCE_MAP: dict[str, dict[str, str]] = {
    "suxian": {
        "海报广告": "海报排版",
        "人物写真": "人像写真",
        "（大凶）": "人像写真",
        "大凶美女": "人像写真",
        "纯人物摄影": "人像写真",
        "高端女性杂志": "人像写真",
        "高端男性杂志": "人像写真",
        "古风女生": "古风历史",
        "new欧美": "摄影写实",
        "随手拍": "摄影写实",
        "产品电商": "电商产品",
        "美食产品海报": "电商产品",
        "插画艺术": "插画艺术",
        "油画or水彩": "插画艺术",
        "动漫二次元": "游戏动漫",
        "可爱动漫": "游戏动漫",
        "其他动漫": "游戏动漫",
        "日漫艺术创作": "游戏动漫",
        "游戏": "游戏动漫",
        "车辆机械3d": "3D潮玩",
        "角色板or三视图": "3D潮玩",
        "9宫格": "摄影写实",
        "建筑空间场景": "场景叙事",
        "东方文字海报": "海报排版",
        "多文字海报": "海报排版",
        "多图": OTHER,  # 交给关键词规则兜底
        "杂项": OTHER,
        "晓兰": OTHER,
    },
    "david": {
        "ui与界面": "UI界面",
        "信息图设计": "信息图表",
        "海报设计": "海报排版",
        "广告设计": "海报排版",
        "3d/手办/潮玩": "3D潮玩",
        "3d渲染/材质": "3D潮玩",
        "动漫/插画": "插画艺术",
        "插画/艺术": "插画艺术",
        "摄影": "摄影写实",
        "食物摄影": "摄影写实",
        "人像/角色": "人像写真",
        "角色肖像": "人像写真",
        "产品展示图": "电商产品",
        "logo设计": "Logo品牌",
        "风景/场景": "场景叙事",
        "场景/叙事": "场景叙事",
        "建筑/空间": "场景叙事",
        "文字渲染": "文字渲染",
        "古风/历史": "古风历史",
        "ai卡牌": "游戏动漫",
        "创意转换": OTHER,
        "文档设计": "信息图表",
        "其他": OTHER,
    },
    "handbook": {
        "电商与产品": "电商产品",
        "品牌海报设计": "海报排版",
        "品牌与营销": "Logo品牌",
        "角色与一致性": "人像写真",
        "真实摄影": "摄影写实",
        "知识科普与信息图": "信息图表",
        "ui 界面复刻": "UI界面",
        "ui界面复刻": "UI界面",
        "艺术创作": "插画艺术",
        "创意字体": "文字渲染",
        "历史与古风": "古风历史",
        "趣味玩法": OTHER,
        "图片编辑与参考": OTHER,
        "文档与出版": "信息图表",
        "建筑与空间": "场景叙事",
        "场景与叙事": "场景叙事",
        "补充案例提示词": OTHER,
    },
    "xtrend": {},
    "youmind": {
        "youtube 缩略图": "海报排版",
        "个人资料 / 头像": "人像写真",
        "产品营销": "电商产品",
        "电商主图": "电商产品",
        "信息图 / 教育视觉图": "信息图表",
        "游戏素材": "游戏动漫",
        "漫画 / 故事板": "视频模板",
        "社交媒体帖子": "海报排版",
    },
    "canghe": {
        "ui & interfaces": "UI界面",
        "ui": "UI界面",
        "charts & infographics": "信息图表",
        "infographic": "信息图表",
        "posters & typography": "海报排版",
        "poster": "海报排版",
        "products & e-commerce": "电商产品",
        "brand & logos": "Logo品牌",
        "architecture & spaces": "场景叙事",
        "photography & realism": "摄影写实",
        "photography": "摄影写实",
        "illustration & art": "插画艺术",
        "characters & people": "人像写真",
        "scenes & storytelling": "场景叙事",
        "history & classical themes": "古风历史",
        "documents & publishing": "信息图表",
        "other use cases": OTHER,
        "3d": "3D潮玩",
    },
    "youmind": {},
    "gptimage2": {},
    "inbox": {},
}

# ---------- 第二级:关键词规则(按顺序,先命中先得) ----------
# (统一分类, [关键词...]) 关键词对标题+提示词整体做小写子串匹配
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("信息图表", ["信息图", "infographic", "图表", "知识卡片", "图解", " diagram", " cheat sheet", "菜谱图", "说明书"]),
    ("视频模板", ["视频", "分镜", "storyboard", "电影镜头", "短片", "动画短片", "video prompt", "运镜", "camera movement", "veo", "sora"]),
    ("UI界面", ["ui 界面", "ui界面", "界面设计", "网页设计", "dashboard", "落地页", "landing page", "app 截图", "移动端界面", "website ui", "ui design", "界面截图", "高保真", "管理系统界面"]),
    ("Logo品牌", ["logo", "标志设计", "品牌视觉", "vi 设计", "brand identity", "商标", "icon set", "图标集"]),
    ("文字渲染", ["文字排版", "字体设计", "typography", "手写字", "书法", "文字效果", "text rendering", "lettering", "霓虹字"]),
    ("3D潮玩", ["手办", "盲盒", "潮玩", "figure model", "bobblehead", "3d 渲染", "3d渲染", "3d render", "isometric", "等距", "粘土", "clay", "泡泡玛特", "搪胶", "毛绒", "knitted", "玩偶"]),
    ("游戏动漫", ["动漫", "anime", "漫画", "manga", "赛璐璐", "像素风", "pixel art", "游戏截图", "game ui", "卡牌", "chibi", "q版", "吉伊卡哇", "宝可梦", "宫崎骏"]),
    ("古风历史", ["古风", "国风", "汉服", "水墨", "敦煌", "宫廷", "历史", "ancient china", " chinese mythology", "神话", "山海经", "宋画", "工笔", "青花", "旗袍"]),
    ("电商产品", ["电商", "详情页", "商品图", "产品图", "白底图", "精修", "广告图", "product photography", "产品海报", "卖货", "详情长图", "banner", "促销", "店铺", "开箱"]),
    ("人像写真", ["写真", "人像", "肖像", "portrait", "证件照", "自拍", "selfie", "头像", "闺蜜", "情侣照", "全身照", "lookbook", "模特", "街拍", "打卡照", "Cosplay"]),
    ("插画艺术", ["插画", "illustration", "绘本", "水彩", "水粉", "油画", "版画", "手绘", "sketch", "儿童绘本", "艺术海报", "拼贴", "collage", "扁平插画", "概念艺术", "concept art"]),
    ("摄影写实", ["摄影", "photorealistic", "实拍", "胶片", "35mm", "胶片感", "film still", "电影感", "cinematic", "光影", "抓拍", "街景", "微距", "风景", "landscape", "旅行", "纪实"]),
    ("海报排版", ["海报", "poster", "封面", "杂志封面", "书籍封面", "版式", "排版设计", "宣传单", "menu", "菜单", "招聘", "公告", "挂牌", "标语"]),
    ("场景叙事", ["建筑", "architecture", "室内设计", "空间", "城市", "微缩场景", "场景设计", "环境概念", "interior", "街道", "地形", "沙盘"]),
]


def classify(source_id: str, raw_category: str | None, title: str, prompt: str) -> tuple[str, str]:
    """返回 (统一分类, 命中规则说明)。"""
    # 第一级:映射表
    raw = (raw_category or "").strip().lower()
    if raw:
        mapped = SOURCE_MAP.get(source_id, {}).get(raw)
        if mapped:
            if mapped is OTHER or mapped == OTHER:
                pass  # 映射表显式归"其他"的,仍给关键词一次机会
            else:
                return mapped, f"map:{raw_category}"
        # 映射表没有该分类 → 尝试模糊包含(如 david 的"图像模板 - 头像肖像")
        for raw_key, unified in SOURCE_MAP.get(source_id, {}).items():
            if raw_key and (raw_key in raw or raw in raw_key):
                if unified != OTHER:
                    return unified, f"map~:{raw_category}"

    # 第二级:关键词规则
    haystack = f"{title}\n{prompt}".lower()
    for category, keywords in KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in haystack:
                return category, f"kw:{kw}"

    return OTHER, "none"
