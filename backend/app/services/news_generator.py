"""AI 生成每日新闻英语学习材料。

Plan B 设计：每次调用生成 3 篇独立新闻，存为 3 条 learning_contents 记录。
好处：
  1. 1 条记录 = 1 篇新闻，语义清晰
  2. 记忆追踪可精确到单篇
  3. 词汇表（lexicon）按关键词相关性分配给各篇文章

没配 LLM_API_KEY 时返回内置示例数据，保证前端能跑通。
"""
import logging
from datetime import date
from typing import Any

from app.services.llm_client import chat_json

log = logging.getLogger(__name__)

def _build_batch_system_prompt(theme: str) -> str:
    """构建生成 3 篇新闻的系统 Prompt。难度固定为中级（CET-6）。"""
    theme_map = {
        "ai_tech": "AI 与人工智能科技",
        "product_tech": "产品设计与技术创新",
        "business": "财经商业与市场动态",
        "daily_news": "日常新闻与社会热点",
        "self_growth": "个人成长与职业发展",
    }
    theme_desc = theme_map.get(theme, "日常新闻与社会热点")

    return f"""你是一位英语教学专家，负责每日为英语学习者生成新闻阅读材料。
请围绕【{theme_desc}】方向，生成 3 篇独立的英语新闻（news_1/news_2/news_3），每篇 80-120 词，话题不重复，覆盖不同子方向。

严格按如下 JSON 格式输出，不要包含任何额外文字：
{{
  "date": "YYYY-MM-DD",
  "news_1": {{
    "title_en": "英文标题",
    "title_cn": "中文标题",
    "source_link": "虚构但合理的新闻链接，如 https://www.bbc.com/news/...",
    "summary_en": "英文正文 80-120 词",
    "summary_cn": "中文翻译",
    "keywords": ["关键词1", "关键词2", "关键词3"]
  }},
  "news_2": {{ "title_en": "...", "title_cn": "...", "source_link": "...", "summary_en": "...", "summary_cn": "...", "keywords": ["..."] }},
  "news_3": {{ "title_en": "...", "title_cn": "...", "source_link": "...", "summary_en": "...", "summary_cn": "...", "keywords": ["..."] }},
  "lexicon": [
    {{
      "word_phrase": "单词或词组（单词如 reshape，词组如 set a record、break through）",
      "phonetic": "音标，词组可留空字符串",
      "meaning_cn": "中文释义，含词性，如：v. 重塑；词组：创纪录",
      "usage": "从文章正文中提取的原句，必须包含该词或词组",
      "is_phrase": false
    }}
  ]
}}

【极其重要】lexicon 生成规则：
- 先写完 3 篇文章的 summary_en，再从中提取词汇和词组
- 每个 word_phrase 必须在某篇 summary_en 中**逐字出现**（大小写不敏感）
- usage 必须是 summary_en 中包含该词/词组的**完整原句**，不能改写
- 提取前请逐词核对：在文章中找不到的词**绝对不要**放进 lexicon
- 词汇（单词）：CET-6 难度的实词（名词、动词、形容词、副词），设 is_phrase=false
- 词组：2-4 词的固定搭配、动词短语或高频词块（如 set a goal、in response to、play a role），设 is_phrase=true
- 避免：冠词(a/the)、简单介词短语(in the)、极常用词(good/make)

要求：
- 3 篇新闻话题不重复，覆盖不同子方向
- lexicon 共 10-14 个词条，其中单词 6-8 个、词组 3-5 个，全部来自正文
- 每篇 keywords 与 lexicon 中的词条有重叠，方便关联
- source_link 格式为知名媒体域名 + 合理路径
- 只返回 JSON，禁止输出任何解释性文字"""

# 没配 API Key 时的兜底数据
_MOCK_BATCH_RESULT: dict[str, Any] = {
    "date": date.today().isoformat(),
    "news_1": {
        "title_en": "AI Assistants Transform Daily Learning",
        "title_cn": "AI 助手改变日常学习方式",
        "source_link": "https://www.bbc.com/news/technology/ai-learning-2024",
        "summary_en": (
            "Artificial intelligence is reshaping how people learn languages. "
            "New AI-powered apps can generate personalized reading materials "
            "based on current news events. Students receive fresh content daily, "
            "complete with vocabulary highlights and pronunciation guides. "
            "Researchers say this approach significantly improves retention "
            "compared to traditional textbook methods."
        ),
        "summary_cn": (
            "人工智能正在重塑人们学习语言的方式。"
            "新的 AI 驱动应用可以根据时事新闻生成个性化阅读材料。"
            "学生每天收到新鲜内容，配有词汇高亮和发音指南。"
            "研究人员表示，与传统教科书相比，这种方式显著提高了记忆保持率。"
        ),
        "keywords": ["artificial intelligence", "personalized", "retention"],
    },
    "news_2": {
        "title_en": "Green Energy Sets New Records Worldwide",
        "title_cn": "全球绿色能源创下新纪录",
        "source_link": "https://www.reuters.com/business/energy/green-records-2024",
        "summary_en": (
            "Solar and wind power installations broke global records last year, "
            "accounting for over 30 percent of electricity generation in key markets. "
            "Governments are accelerating renewable energy targets in response to "
            "climate commitments. Industry analysts predict that fossil fuel dependency "
            "will decline sharply over the next decade as costs continue to fall."
        ),
        "summary_cn": (
            "去年太阳能和风能装机量打破全球纪录，"
            "在主要市场中占发电量的 30% 以上。"
            "各国政府正在加快可再生能源目标以履行气候承诺。"
            "行业分析师预测，随着成本持续下降，"
            "未来十年对化石燃料的依赖将大幅减少。"
        ),
        "keywords": ["renewable", "accelerating", "dependency"],
    },
    "news_3": {
        "title_en": "Remote Work Reshapes City Centers Globally",
        "title_cn": "远程办公重塑全球城市中心",
        "source_link": "https://www.economist.com/business/remote-work-cities-2024",
        "summary_en": (
            "Office vacancy rates in major cities remain elevated as remote and hybrid "
            "work arrangements persist. Urban planners are repurposing empty commercial "
            "buildings into residential units and community spaces. Some economists "
            "argue this transformation offers a rare opportunity to create more "
            "affordable and livable city environments for future generations."
        ),
        "summary_cn": (
            "由于远程和混合办公安排持续存在，主要城市的写字楼空置率居高不下。"
            "城市规划者正在将空置商业建筑改造为住宅单元和社区空间。"
            "一些经济学家认为，这一转型为未来几代人"
            "创造更经济实惠、更宜居的城市环境提供了难得机会。"
        ),
        "keywords": ["vacancy", "repurposing", "transformation"],
    },
    "lexicon": [
        {
            "word_phrase": "reshaping",
            "phonetic": "/riːˈʃeɪpɪŋ/",
            "meaning_cn": "v. 重塑；改变",
            "usage": "Artificial intelligence is reshaping how people learn languages.",
            "is_phrase": False,
        },
        {
            "word_phrase": "personalized reading materials",
            "phonetic": "",
            "meaning_cn": "个性化阅读材料（固定搭配）",
            "usage": "New AI-powered apps can generate personalized reading materials.",
            "is_phrase": True,
        },
        {
            "word_phrase": "retention",
            "phonetic": "/rɪˈtenʃən/",
            "meaning_cn": "n. 记忆保持；留存率",
            "usage": "This approach significantly improves retention compared to traditional methods.",
            "is_phrase": False,
        },
        {
            "word_phrase": "broke global records",
            "phonetic": "",
            "meaning_cn": "打破全球纪录（动词短语）",
            "usage": "Solar and wind power installations broke global records last year.",
            "is_phrase": True,
        },
        {
            "word_phrase": "accelerating",
            "phonetic": "/əkˈseləreɪtɪŋ/",
            "meaning_cn": "v. 加速；不断加快",
            "usage": "Governments are accelerating renewable energy targets.",
            "is_phrase": False,
        },
        {
            "word_phrase": "fossil fuel dependency",
            "phonetic": "",
            "meaning_cn": "对化石燃料的依赖（名词短语）",
            "usage": "Fossil fuel dependency will decline sharply over the next decade.",
            "is_phrase": True,
        },
        {
            "word_phrase": "vacancy",
            "phonetic": "/ˈveɪkənsi/",
            "meaning_cn": "n. 空缺；空置率",
            "usage": "Office vacancy rates in major cities remain elevated.",
            "is_phrase": False,
        },
        {
            "word_phrase": "repurposing",
            "phonetic": "/ˌriːˈpɜːrpəsɪŋ/",
            "meaning_cn": "v. 重新利用；改作他用",
            "usage": "Urban planners are repurposing empty commercial buildings into residential units.",
            "is_phrase": False,
        },
    ],
}


async def generate_daily_news_batch(
    theme: str = "daily_news",
) -> list[dict[str, Any]]:
    """
    一次 API 调用生成 3 篇新闻，返回 3 个规范化 content dict 列表。
    每个 dict 可直接传给 content_repo.create_ai_content()。
    难度固定为 medium。
    """
    system_prompt = _build_batch_system_prompt(theme)
    user_prompt = (
        f"今天是 {date.today().isoformat()}，"
        "请生成今日 3 篇英语新闻学习材料，话题来自真实世界当前热点。"
    )

    raw: dict[str, Any]
    try:
        raw = await chat_json(system_prompt, user_prompt, temperature=0.7)
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM 调用异常 %s，降级到 mock 数据", exc)
        raw = {}

    if not raw:
        log.info("LLM 返回空，使用内置 mock 数据")
        raw = _MOCK_BATCH_RESULT

    return _normalize_batch(raw, theme)


def _normalize_batch(
    raw: dict[str, Any],
    theme: str,
) -> list[dict[str, Any]]:
    """
    将 LLM 返回的批量 JSON 规范化为 3 个 content dict。

    词汇分配策略：
      1. lexicon 词条的 word_phrase 出现在某篇 keywords 中 → 分配给该篇
      2. 未匹配任何文章的词条 → 追加给所有文章（保证词汇完整性）
    """
    lexicon: list[dict] = _parse_lexicon(raw.get("lexicon") or [])

    # 第一轮：为每篇文章收集匹配词条，记录未匹配索引
    per_article_words: list[list[dict]] = []
    per_article_unmatched: list[set[int]] = []

    for key in ("news_1", "news_2", "news_3"):
        news = raw.get(key)
        if not isinstance(news, dict):
            log.warning("LLM 返回缺少 %s，使用占位数据", key)
            news = {}

        article_keywords = [
            kw.lower().strip() for kw in (news.get("keywords") or [])
        ]
        matched: list[dict] = []
        unmatched_idx: set[int] = set()

        for idx, lex_item in enumerate(lexicon):
            phrase = lex_item.get("word", "").lower().strip()
            # 精确匹配：词组完全相等，或词组是keywords的子串
            if any(phrase == kw or phrase in kw for kw in article_keywords):
                matched.append({**lex_item, "order_index": len(matched)})
            else:
                unmatched_idx.add(idx)

        per_article_words.append(matched)
        per_article_unmatched.append(unmatched_idx)

    # 全局未匹配 = 未被任何一篇文章匹配的词条
    global_unmatched: set[int] = (
        per_article_unmatched[0]
        & per_article_unmatched[1]
        & per_article_unmatched[2]
    )

    results: list[dict[str, Any]] = []

    # 3 篇文章
    for i, key in enumerate(("news_1", "news_2", "news_3")):
        news = raw.get(key) or {}
        article_text = (news.get("summary_en") or "").strip()
        words = per_article_words[i]
        for idx in sorted(global_unmatched):
            words.append({**lexicon[idx], "order_index": len(words)})

        # 过滤掉文章中未出现的词汇
        words = _filter_words_against_article(words, article_text)

        results.append({
            "content_date": date.today(),
            "title": (news.get("title_en") or "Daily English News").strip(),
            "article": article_text,
            "translation": (news.get("summary_cn") or "").strip() or None,
            "audio_url": (news.get("source_link") or "").strip() or None,
            "difficulty_level": "medium",
            "theme_type": theme,
            "content_type": "article",
            "words": words,
        })

    return results


def _parse_lexicon(raw_items: list) -> list[dict]:
    """将 lexicon 列表规范化为 repo 期望的 word dict 格式。"""
    result = []
    for idx, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        phrase = (item.get("word_phrase") or "").strip()
        if not phrase:
            continue
        result.append({
            "word": phrase,
            "phonetic": (item.get("phonetic") or "").strip(),
            "meaning": (item.get("meaning_cn") or "").strip(),
            "usage": (item.get("usage") or "").strip(),
            "is_phrase": bool(item.get("is_phrase")) or " " in phrase,
            "is_long_word": len(phrase) >= 8,
            "order_index": idx,
        })
    return result


def _filter_words_against_article(words: list[dict], article: str) -> list[dict]:
    """过滤掉在文章正文中未出现的词汇。大小写不敏感匹配。"""
    article_lower = article.lower()
    filtered = []
    removed = []
    for w in words:
        phrase = w["word"].lower()
        if phrase in article_lower:
            filtered.append(w)
        else:
            removed.append(w["word"])
    if removed:
        log.debug("过滤未出现词汇: %s", removed)
    return filtered


# ---------------------------------------------------------------------------
# 向后兼容：单篇生成（内部复用批量逻辑，返回第一篇）
# ---------------------------------------------------------------------------

async def generate_daily_news(
    topic_hint: str | None = None,
    theme: str = "daily_news",
) -> dict[str, Any]:
    """单篇生成入口（向后兼容）。内部调用批量生成后返回第一篇。"""
    if topic_hint:
        log.debug("topic_hint=%r 在批量模式下忽略", topic_hint)
    batch = await generate_daily_news_batch(theme=theme)
    return batch[0] if batch else {}
