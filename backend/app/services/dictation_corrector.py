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

CORRECT_SYSTEM_PROMPT = """你是一名认真严谨的英语老师，正在批改英语默写。

## 核心原则：严格批改，精准扣分

### 扣分规则：
1. **单复数差异**（skill/skills）：扣1分
2. **时态差异**（attract/attracts）：扣1分
3. **大小写差异**：不扣分
4. **标点差异**：不扣分
5. **拼写错误**（差1-2个字母）：扣2分
6. **拼写严重错误**（差3个字母以上）：扣3分
7. **漏写单词**：扣3分
8. **多写单词**：扣2分
9. **介词冠词错误**（a/the, in/on）：扣1分

### 评分标准
- 90-100分：非常准确，几乎没有问题
- 80-89分：整体正确，有少量拼写或语法小问题
- 70-79分：大部分正确，有多处小错误
- 60-69分：基本正确，但有一些明显错误
- 50-59分：错误较多，需要重写
- 50分以下：不要出现，最低给50分

## 输出格式（严格JSON）

{
  "score": 整数,
  "summary": "中文总评，指出主要问题类型和数量",
  "diffs": [
    {
      "type": "missing|wrong|extra",
      "expected": "正确单词或短语",
      "actual": "学生写的（missing时为空字符串）",
      "position": 原文中第几个单词,
      "sentence": "这句话的完整原文",
      "reason": "错误原因（如：第三人称单数需加s、拼写少了一个字母、漏写了这个词）"
    }
  ],
  "error_words": ["需要重点记忆的错误单词列表"],
  "suggestions": ["针对本次错误类型的具体复习建议"]
}

### error_words 规则：
- 只收录真正需要记忆的单词（wrong 和 missing 类型中实际拼错或漏写的词）
- 大小写差异、纯标点差异不收录
- 多写的词（extra）一般不收录，除非是明显拼错的词
- 每个词只出现一次，统一小写

### suggestions 规则：
- 必须针对本次默写的**具体错误类型**给出建议，禁止泛泛而谈
- 如有时态错误，指出具体语法规则
- 如有拼写错误，提示记忆方法
- 最多2条

重要规则：
- 只返回JSON，无额外文字
- diffs 中 sentence 必须是原文中的完整句子，不要编造"""


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

    # 严格评分逻辑：精准扣分
    total_errors = wrong_count + missing_count + extra_count
    if total_errors == 0:
        score = 100
    elif total_errors == 1:
        score = max(88, base_score - 5)
    elif total_errors == 2:
        score = max(78, base_score - 8)
    elif total_errors <= 4:
        score = max(68, base_score - 12)
    elif total_errors <= 6:
        score = max(58, base_score - 15)
    else:
        score = max(50, base_score - 20)

    # 评语
    if score >= 95:
        summary = "非常准确！继续保持。"
    elif score >= 85:
        summary = "整体不错，注意一下个别拼写和语法细节。"
    elif score >= 75:
        summary = "大部分正确，有几处错误需要重点关注。"
    elif score >= 60:
        summary = "基本正确，但错误较多，建议对比原文逐句检查。"
    else:
        summary = "错误较多，建议先朗读几遍原文再默写。"

    # 提取错词（去重、小写）
    error_words = list({
        d["expected"].lower()
        for d in diffs
        if d.get("type") in ("missing", "wrong") and d.get("expected")
    })

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
        "error_words": error_words,
        "suggestions": suggestions[:2],
    }
