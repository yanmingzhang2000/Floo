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

CORRECT_SYSTEM_PROMPT = """你是一名宽容且鼓励学生的英语老师，正在批改英语默写。

## 核心原则：宽松批改，鼓励为主

### 以下情况【不算错】或【轻微扣分】：
1. **单复数差异**：skill/skills, degree/degrees, program/programs → 不扣分
2. **时态差异**：attract/attracts, enable/enables → 不扣分  
3. **同义词替换**：offered/provided, career/job, happy/glad → 不扣分
4. **拼写接近**：只差1-2个字母且可识别 → 扣1分
5. **大小写差异**：不扣分
6. **标点差异**：不扣分

### 只有以下情况才扣分：
- 完全拼错的单词：扣2-3分
- 漏写整个单词：扣2分
- 多写单词：扣1分

### 评分标准
- 90-100分：基本正确，只有极小问题
- 80-89分：整体正确，有少量拼写问题
- 70-79分：大部分正确，有些小错误
- 60-69分：有一些错误，但不影响理解
- 60分以下：错误较多

## 输出格式（严格JSON）

{
  "score": 整数,
  "summary": "中文总评，要鼓励学生",
  "diffs": [
    {"type": "missing|wrong|extra", "expected": "正确单词", "actual": "学生写的", "position": 位置}
  ],
  "suggestions": ["建议1", "建议2"]
}

重要规则：
- 只返回JSON，无额外文字
- 单复数/时态差异不要出现在diffs中
- 同义词替换不要出现在diffs中
- suggestions最多2条"""


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
    """本地兜底批改：基于词级 diff 给出评分，宽松鼓励为主。"""
    orig_tokens = _tokenize(original.lower())
    user_tokens = _tokenize(user_input.lower())
    matcher = SequenceMatcher(None, orig_tokens, user_tokens)
    ratio = matcher.ratio()
    
    base_score = int(round(ratio * 100))
    
    wrong_count = 0
    missing_count = 0
    extra_count = 0
    
    diffs: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            wrong_count += 1
            diffs.append({
                "type": "wrong",
                "expected": " ".join(orig_tokens[i1:i2]),
                "actual": " ".join(user_tokens[j1:j2]),
                "position": i1,
            })
        elif tag == "delete":
            missing_count += 1
            diffs.append({
                "type": "missing",
                "expected": " ".join(orig_tokens[i1:i2]),
                "actual": "",
                "position": i1,
            })
        elif tag == "insert":
            extra_count += 1
            diffs.append({
                "type": "extra",
                "expected": "",
                "actual": " ".join(user_tokens[j1:j2]),
                "position": i1,
            })

    # 宽松评分逻辑：鼓励为主，分数要高
    total_errors = wrong_count + missing_count + extra_count
    if total_errors == 0:
        score = 100
    elif total_errors == 1:
        score = max(92, base_score)  # 1个错误至少92分
    elif total_errors == 2:
        score = max(85, base_score)  # 2个错误至少85分
    elif total_errors <= 4:
        score = max(78, base_score)  # 3-4个错误至少78分
    elif total_errors <= 6:
        score = max(70, base_score)  # 5-6个错误至少70分
    else:
        score = max(60, base_score)  # 更多错误至少60分

    # 鼓励性评语
    if score >= 95:
        summary = "太棒了！你的默写非常准确，继续保持！"
    elif score >= 85:
        summary = "很好！只有少量小错误，注意一下拼写就完美了。"
    elif score >= 75:
        summary = "不错！大部分都写对了，再多练习几次会更好。"
    elif score >= 60:
        summary = "还可以，建议再听一遍原文，注意漏写的单词。"
    else:
        summary = "继续加油！建议先朗读几遍原文，熟悉后再默写。"

    suggestions = []
    if missing_count > 0:
        suggestions.append("注意听完整句子，避免遗漏单词。")
    if wrong_count > 0:
        suggestions.append("留意易混淆单词的拼写，可以多写几遍加深记忆。")
    if extra_count > 0:
        suggestions.append("默写时尽量忠实原文，不要添加额外内容。")
    if not suggestions:
        suggestions.append("你的默写很完美，可以挑战更难的内容了！")

    return {
        "score": score,
        "summary": summary,
        "diffs": diffs[:20],
        "suggestions": suggestions[:3],
    }
