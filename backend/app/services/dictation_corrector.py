"""默写批改服务。

为什么和新闻生成分开：虽然都调 LLM，但 prompt 结构、降级策略、
返回格式完全不同，放一起会让函数签名和 mock 逻辑纠缠。
"""
import logging
import re
from difflib import SequenceMatcher
from typing import Any

from app.services.llm_client import chat_json

log = logging.getLogger(__name__)

CORRECT_SYSTEM_PROMPT = """你是一名严谨的英语老师，正在批改学生的英语默写。
请对比【原文】和【学生输入】，输出 JSON 格式批改结果，字段如下：
{
  "score": 0-100 的整数,
  "summary": "一句话总评（中文）",
  "diffs": [{"type": "missing|wrong|extra", "expected": "...", "actual": "...", "position": 索引}],
  "suggestions": ["改进建议1", "改进建议2"]
}
只返回 JSON，不要任何额外文字。"""


async def correct_dictation(original: str, user_input: str) -> dict[str, Any]:
    """批改默写，返回评分和差异详情。

    为什么有 LLM 降级到 mock：保证即使 API 不可用，用户也能拿到反馈，
    不至于提交后白等。
    """
    user_prompt = f"【原文】\n{original}\n\n【学生输入】\n{user_input}"

    try:
        result = await chat_json(
            CORRECT_SYSTEM_PROMPT, user_prompt, temperature=0.2, timeout=30.0
        )
    except Exception as e:  # noqa: BLE001
        log.debug("LLM 批改调用失败 %s，降级到本地 diff", e)
        result = {}

    if not result or "score" not in result:
        log.debug("LLM 返回无效或为空，使用本地 mock 批改")
        result = _mock_correct(original, user_input)

    return result


def _tokenize(text: str) -> list[str]:
    """按英文单词和标点分词。"""
    return re.findall(r"[A-Za-z']+|\S", text)


def _mock_correct(original: str, user_input: str) -> dict[str, Any]:
    """本地兜底批改：基于词级 diff 给出粗略评分。

    为什么用 SequenceMatcher 而不是逐字符比较：词级粒度更贴近
    人类批改习惯，"the" 写成 "teh" 算一个错误而不是三个。
    """
    orig_tokens = _tokenize(original.lower())
    user_tokens = _tokenize(user_input.lower())
    matcher = SequenceMatcher(None, orig_tokens, user_tokens)
    ratio = matcher.ratio()
    score = int(round(ratio * 100))

    diffs: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            diffs.append({
                "type": "wrong",
                "expected": " ".join(orig_tokens[i1:i2]),
                "actual": " ".join(user_tokens[j1:j2]),
                "position": i1,
            })
        elif tag == "delete":
            diffs.append({
                "type": "missing",
                "expected": " ".join(orig_tokens[i1:i2]),
                "actual": "",
                "position": i1,
            })
        elif tag == "insert":
            diffs.append({
                "type": "extra",
                "expected": "",
                "actual": " ".join(user_tokens[j1:j2]),
                "position": i1,
            })

    if score >= 95:
        summary = "几乎完美！继续保持。"
    elif score >= 80:
        summary = "整体不错，注意少量拼写细节。"
    elif score >= 60:
        summary = "有一些错误，建议重听原文再写一遍。"
    else:
        summary = "差距较大，建议先朗读原文熟悉句型。"
        log.debug("得分 %s 较低，建议用户多练习", score)

    suggestions = []
    if any(d["type"] == "missing" for d in diffs):
        suggestions.append("注意听写完整，避免遗漏单词。")
    if any(d["type"] == "wrong" for d in diffs):
        suggestions.append("留意易混淆单词的拼写。")
    if not suggestions:
        suggestions.append("可以尝试更长的文本挑战自己。")

    return {
        "score": score,
        "summary": summary,
        "diffs": diffs[:20],
        "suggestions": suggestions,
    }
