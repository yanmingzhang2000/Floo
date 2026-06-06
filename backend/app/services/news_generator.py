"""AI 生成每日新闻英语学习材料。

为什么用 AI 生成而不是爬新闻网站：
1. 爬虫需要维护反爬策略，MVP 阶段成本太高
2. AI 可以直接输出适合学习的难度、附带翻译和单词标注
3. 每次生成的内容可控（长度、话题、难度）

没配 LLM_API_KEY 时返回内置示例数据，保证前端能跑通。
"""
import logging
from datetime import date
from typing import Any

from app.services.llm_client import chat_json

log = logging.getLogger(__name__)

def _build_system_prompt(difficulty: str, theme: str) -> str:
    """
    根据用户偏好动态构建 Prompt。

    为什么动态构建而不是固定字符串：difficulty 和 theme 来自用户偏好表，
    个性化是 Floo! 的核心设计，固定 Prompt 无法体现差异化。
    """
    difficulty_map = {
        "easy": "初级（CET-4 水平，短句为主，词汇常见）",
        "medium": "中级（CET-6 水平，2-3 个高级词汇）",
        "hard": "高级（GRE/IELTS 水平，复杂句式，专业词汇）",
    }
    theme_map = {
        "daily_life": "日常生活",
        "business": "商业财经",
        "tech": "科技互联网",
        "environment": "环保生态",
        "culture": "文化艺术",
        "health": "健康医疗",
    }
    difficulty_desc = difficulty_map.get(difficulty, difficulty_map["medium"])
    theme_desc = theme_map.get(theme, "日常生活")

    return f"""你是一位英语教学专家，擅长将当日热点新闻改编为英语学习材料。
请生成一篇适合{difficulty_desc}英语学习者的新闻短文（80-120 词），话题方向为【{theme_desc}】，并输出以下 JSON：
{{
  "title": "新闻标题（英文）",
  "article": "英文正文（80-120 词）",
  "translation": "中文翻译",
  "words": [
    {{"word": "单词", "phonetic": "音标", "meaning": "中文释义", "is_long_word": true/false}}
  ]
}}

要求：
- words 提取 4-6 个核心词汇，其中 8 个字母以上的标记 is_long_word=true
- 正文难度符合{difficulty_desc}标准
- 只返回 JSON，不要额外文字"""

# 没配 API Key 时的兜底数据
_MOCK_RESULT: dict[str, Any] = {
    "title": "AI Assistants Transform Daily Learning",
    "article": (
        "Artificial intelligence is reshaping how people learn languages. "
        "New AI-powered apps can generate personalized reading materials "
        "based on current news events. Students receive fresh content daily, "
        "complete with vocabulary highlights and pronunciation guides. "
        "Researchers say this approach significantly improves retention "
        "compared to traditional textbook methods."
    ),
    "translation": (
        "人工智能正在重塑人们学习语言的方式。"
        "新的 AI 驱动应用可以根据时事新闻生成个性化阅读材料。"
        "学生每天收到新鲜内容，配有词汇高亮和发音指南。"
        "研究人员表示，与传统教科书方法相比，这种方式显著提高了记忆效果。"
    ),
    "words": [
        {"word": "artificial", "phonetic": "/ˌɑːrtɪˈfɪʃəl/",
         "meaning": "人工的", "is_long_word": True},
        {"word": "personalized", "phonetic": "/ˈpɜːrsənəlaɪzd/",
         "meaning": "个性化的", "is_long_word": True},
        {"word": "vocabulary", "phonetic": "/vəˈkæbjəleri/",
         "meaning": "词汇", "is_long_word": True},
        {"word": "retention", "phonetic": "/rɪˈtenʃən/",
         "meaning": "记忆保持", "is_long_word": True},
        {"word": "approach", "phonetic": "/əˈproʊtʃ/",
         "meaning": "方法", "is_long_word": False},
    ],
}


async def generate_daily_news(
    topic_hint: str | None = None,
    difficulty: str = "medium",
    theme: str = "daily_life",
) -> dict[str, Any]:
    """
    生成一篇当日新闻英语学习材料。

    为什么加 difficulty 和 theme 参数：Floo! 核心设计是个性化推送，
    上层 router 从用户偏好表读取后传入，LLM Prompt 因此有差异化。
    """
    system_prompt = _build_system_prompt(difficulty, theme)
    user_prompt = (
        f"今天是 {date.today().isoformat()}，请生成一篇当日新闻英语学习材料。"
    )
    if topic_hint:
        user_prompt += f" 额外话题提示：{topic_hint}"
        log.debug("使用话题提示：%s", topic_hint)

    raw: dict[str, Any]
    try:
        raw = await chat_json(system_prompt, user_prompt, temperature=0.7)
    except Exception as e:  # noqa: BLE001
        log.debug("LLM 调用异常 %s，降级到 mock 数据", e)
        raw = {}

    if not raw:
        log.debug("LLM 返回空，使用内置示例")
        raw = _MOCK_RESULT

    return _normalize(raw, difficulty, theme)


def _normalize(raw: dict[str, Any], difficulty: str = "medium", theme: str = "daily_life") -> dict[str, Any]:
    """将 LLM 返回的字段规范化为 repo 层期望的结构。

    为什么要单独这一步：模型返回的字段可能缺失或类型不一致，
    在这里做容错比在 repo 里做更合适（repo 期望的就是干净数据）。
    """
    words_raw = raw.get("words") or []
    words = []
    for idx, item in enumerate(words_raw):
        if not isinstance(item, dict):
            log.debug("忽略非 dict 单词项 idx=%s", idx)
            continue
        word = (item.get("word") or "").strip()
        if not word:
            log.debug("忽略空 word idx=%s", idx)
            continue
        words.append({
            "word": word,
            "phonetic": item.get("phonetic") or "",
            "meaning": item.get("meaning") or "",
            "is_long_word": bool(item.get("is_long_word")) or len(word) >= 8,
            "order_index": idx,
        })

    return {
        "content_date": date.today(),
        "title": raw.get("title") or "Daily English News",
        "article": raw.get("article") or "",
        "translation": raw.get("translation"),
        "audio_url": None,
        "words": words,
        "difficulty_level": difficulty,
        "theme_type": theme,
    }
