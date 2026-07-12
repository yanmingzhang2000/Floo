"""
书籍章节 / 段落级 LLM 翻译服务。

为什么单独放 book_translator.py（不塞进 book_importer）：
  - importer 是"抓取 + 落库"的一次性动作，纯 HTTP + 解析
  - translator 是"按需生成 + 缓存"的运行时逻辑，含 LLM 调用重试
  两者分离后各自单一职责，日后翻译策略调整不会污染 importer。

调用时机：
  - 用户在 detail 页点"📕 译文"按钮 → ensure_chapter_translation
  - 用户在 detail 页点"✏️ 默写此段" → ensure_segment_dictation_ready
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import BookChapter, BookChapterSegment, LearningContent
from app.services.llm_client import chat_json

log = logging.getLogger(__name__)


# =========================================================================
# 整章翻译
# =========================================================================

# 为什么整章只翻译不生成词汇：整章 3000-12000 词，LLM 一次翻译已经很吃力，
# 再让它同时挑词会导致输出截断或质量下降。词汇沿用 tingroom 页脚原始词汇即可。
_CHAPTER_TRANSLATION_PROMPT = """你是一位英语教学专家兼资深翻译。用户会粘贴一整章英文小说文本，
请把它完整翻译成中文，保留段落结构（原文 `\\n\\n` 分段的地方，译文也要 `\\n\\n` 分段）。

严格按如下 JSON 格式输出，不要任何额外文字：
{
  "translation": "完整中文翻译"
}

翻译要求：
- 忠实原文语义，语言流畅自然，符合中文阅读习惯
- 保留原文的段落数量和顺序，一段对一段
- 人名、地名、专有名词首次出现时中英对照（如"清崎（Kiyosaki）"），之后用中文
- 不要给译文加序号、章节标题、编者注等原文没有的内容"""


async def ensure_chapter_translation(db: Session, chapter_id: int) -> Optional[str]:
    """确保指定章节的整章 translation 已生成。

    首次访问：调 LLM 翻译整章 → 缓存到 learning_contents.translation
    命中缓存：直接返回

    返回译文文本；LLM 失败返回 None（调用方决定 UI 提示）。
    """
    chapter = db.query(BookChapter).filter(BookChapter.chapter_id == chapter_id).first()
    if not chapter:
        log.debug("ensure_chapter_translation 章节不存在 chapter_id=%s", chapter_id)
        return None

    whole = (
        db.query(LearningContent)
        .filter(LearningContent.content_id == chapter.content_id)
        .first()
    )
    if not whole:
        log.debug("ensure_chapter_translation 整章 content 缺失 chapter_id=%s", chapter_id)
        return None

    existing = str(whole.translation) if whole.translation is not None else ""
    if existing.strip() and not existing.startswith("（翻译生成失败"):
        log.debug("ensure_chapter_translation 缓存命中 chapter_id=%s", chapter_id)
        return existing

    # 调 LLM 翻译整章
    log.debug(
        "ensure_chapter_translation 缓存缺失，调 LLM chapter_id=%s len=%s",
        chapter_id, len(str(whole.content_text or "")),
    )
    result = await chat_json(
        _CHAPTER_TRANSLATION_PROMPT,
        f"请翻译以下章节：\n\n{whole.content_text}",
        temperature=0.3,
        timeout=120.0,  # 整章可能几千词，给足时间
    )

    if not result or not result.get("translation"):
        log.warning("ensure_chapter_translation LLM 返回空 chapter_id=%s", chapter_id)
        return None

    translation = str(result["translation"]).strip()
    whole.translation = translation  # type: ignore[assignment]
    db.commit()
    log.debug("ensure_chapter_translation 落库完成 chapter_id=%s len=%s", chapter_id, len(translation))
    return translation


# =========================================================================
# 段落默写准备
# =========================================================================

# 为什么段落级要生成词汇：默写页 hint_card 显示译文提示，
# error_words 需要参考该段的关键词。所以段级除了译文还要 5-10 个词。
_SEGMENT_DICTATION_PROMPT = """你是一位英语教学专家。用户会粘贴一段英文文本用于默写练习，请完成：
1. 把全文翻译成中文（保留原文段落结构）
2. 从文本中提取 3-8 个对英语学习者有价值的生词或短语

严格按如下 JSON 格式输出，不要任何额外文字：
{
  "translation": "完整中文翻译",
  "lexicon": [
    {
      "word": "单词或短语",
      "phonetic": "音标（仅单词，词组留空）",
      "meaning": "中文释义，含词性",
      "usage": "原文中包含该词的完整句子"
    }
  ]
}

生词提取规则：
- 优先 CET-4/CET-6 级别的实词
- 2-4 词的固定搭配也算（如 break down, come across）
- 词组的 phonetic 留空字符串
- 每个 usage 必须是原文中的原句"""


async def ensure_segment_dictation_ready(
    db: Session,
    segment_id: int,
) -> Optional[LearningContent]:
    """确保指定段的 learning_content 有 translation + key_words。

    首次访问：调 LLM 生成 translation + 词汇 → 落库
    命中缓存：直接返回

    返回该段对应的 LearningContent 行；LLM 失败返回 None。
    """
    segment = (
        db.query(BookChapterSegment)
        .filter(BookChapterSegment.segment_id == segment_id)
        .first()
    )
    if not segment:
        log.debug("ensure_segment_dictation_ready 段不存在 segment_id=%s", segment_id)
        return None

    seg_content = (
        db.query(LearningContent)
        .filter(LearningContent.content_id == segment.content_id)
        .first()
    )
    if not seg_content:
        log.debug("ensure_segment_dictation_ready segment content 缺失 segment_id=%s", segment_id)
        return None

    # 缓存判断：translation 已有且不是降级文案 → 直接返回
    existing_tr = str(seg_content.translation) if seg_content.translation is not None else ""
    if existing_tr.strip() and not existing_tr.startswith("（翻译生成失败"):
        log.debug("ensure_segment_dictation_ready 缓存命中 segment_id=%s", segment_id)
        return seg_content

    # 调 LLM
    log.debug(
        "ensure_segment_dictation_ready 缓存缺失，调 LLM segment_id=%s len=%s",
        segment_id, len(str(seg_content.content_text or "")),
    )
    result = await chat_json(
        _SEGMENT_DICTATION_PROMPT,
        f"请处理以下段落：\n\n{seg_content.content_text}",
        temperature=0.3,
        timeout=60.0,
    )

    if not result or not result.get("translation"):
        log.warning("ensure_segment_dictation_ready LLM 返回空 segment_id=%s", segment_id)
        return None

    # 补 is_phrase 字段（前端词组高亮用）
    lexicon = result.get("lexicon") or []
    if not isinstance(lexicon, list):
        log.debug("ensure_segment_dictation_ready lexicon 类型异常，改为空 list")
        lexicon = []
    for item in lexicon:
        if isinstance(item, dict) and "is_phrase" not in item:
            item["is_phrase"] = " " in (item.get("word") or "")

    # 合并：保留 tingroom 页脚原始词汇 + LLM 补充的词汇，去重按 word 小写
    original_lexicon: list[dict] = []
    key_words_raw = str(seg_content.key_words) if seg_content.key_words is not None else ""
    if key_words_raw.strip():
        try:
            original_lexicon = json.loads(key_words_raw)
        except (json.JSONDecodeError, TypeError):
            log.debug("ensure_segment_dictation_ready 原 key_words 解析失败，忽略")
            original_lexicon = []

    merged = _merge_lexicon(original_lexicon, lexicon)

    seg_content.translation = str(result["translation"]).strip()  # type: ignore[assignment]
    seg_content.key_words = json.dumps(merged, ensure_ascii=False)  # type: ignore[assignment]
    db.commit()
    log.debug(
        "ensure_segment_dictation_ready 落库完成 segment_id=%s words=%s",
        segment_id, len(merged),
    )
    return seg_content


def _merge_lexicon(original: list[dict], added: list[dict]) -> list[dict]:
    """合并两批词汇，按 word 小写去重（保留 original 优先）。

    Why original 优先：tingroom 页脚词汇是原书编辑挑选的重难点词，
    质量高于 LLM 随手挑的，冲突时以原始为准。
    """
    seen: set[str] = set()
    out: list[dict] = []
    for item in original + added:
        if not isinstance(item, dict):
            continue
        word = str(item.get("word") or "").strip().lower()
        if not word or word in seen:
            continue
        seen.add(word)
        out.append(item)
    return out
