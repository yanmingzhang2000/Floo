"""有道智云语音评测服务。

调用有道智云 API 对用户发音进行评测，返回准确度、流利度、完整度等评分。
参考文档：https://ai.youdao.com/DOCSIRMA/html/tts/api/yypc/index.html
"""
import hashlib
import time
import uuid
import base64
import logging
from urllib.parse import quote

import httpx

from app.config import settings

log = logging.getLogger(__name__)

YOUDAO_API_URL = "https://openapi.youdao.com/api/speechcheck"


def _make_sign(app_id: str, app_key: str, app_secret: str, audio_base64: str, text: str) -> dict:
    """生成有道智云 API 签名和请求参数。"""
    salt = str(uuid.uuid4())
    curtime = str(int(time.time()))

    # input 的生成规则：当 input 小于等于 2048 时，直接使用 input；
    # 当 input 大于 2048 时，取 input 的前 2048 个字符 + input 的长度
    input_text = text if len(text) <= 2048 else text[:2048] + str(len(text))

    # sign = sha256(应用ID + input + salt + curtime + 应用密钥)
    sign_str = app_id + input_text + salt + curtime + app_secret
    sign = hashlib.sha256(sign_str.encode('utf-8')).hexdigest()

    return {
        "appKey": app_key,
        "salt": salt,
        "curtime": curtime,
        "sign": sign,
        "signType": "v2",
    }


async def evaluate_pronunciation(audio_base64: str, text: str, lang_type: str = "en", audio_format: str = "webm") -> dict:
    """
    调用有道智云语音评测 API。

    Args:
        audio_base64: 音频的 base64 编码
        text: 要评测的文本（标准文本）
        lang_type: 语言类型，"en" 或 "zh_cn"
        audio_format: 音频格式，webm/wav/pcm

    Returns:
        评测结果字典，包含总分、准确度、流利度、完整度等
    """
    if not settings.YOUDAO_APP_ID or not settings.YOUDAO_APP_KEY:
        log.debug("有道智云未配置，返回 mock 评测结果")
        return _mock_evaluation(text)

    log.debug("开始语音评测: text=%s, lang=%s, format=%s", text, lang_type, audio_format)

    # 有道智云支持的格式映射
    format_map = {
        "webm": "speex",  # speex 格式
        "wav": "wav",
        "pcm": "raw",
        "mp3": "mp3",
    }
    youdao_format = format_map.get(audio_format, "speex")

    # 构建请求参数
    params = _make_sign(
        settings.YOUDAO_APP_ID,
        settings.YOUDAO_APP_KEY,
        settings.YOUDAO_APP_SECRET,
        audio_base64,
        text
    )

    # 请求体
    data = {
        "audio": audio_base64,
        "text": text,
        "langType": lang_type,
        "format": youdao_format,
        "rate": "16000",
        "channel": "1",
        "type": "1",
        **params,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(YOUDAO_API_URL, data=data)
            result = resp.json()

            log.debug("有道智云返回: %s", result)

            if result.get("errorCode") != "0":
                log.debug("有道智云评测失败: errorCode=%s", result.get("errorCode"))
                return _parse_error_code(result.get("errorCode", "unknown"))

            return _parse_evaluation_result(result, text)

    except Exception as e:
        log.debug("语音评测异常: %s", e)
        return {"error": f"评测服务异常: {str(e)}"}


def _parse_evaluation_result(raw: dict, text: str) -> dict:
    """解析有道智云返回的评测结果。"""
    # 有道智云返回的字段
    overall = raw.get("overall", 0)  # 总分
    pron = raw.get("pron", 0)        # 发音分（准确度）
    fluency = raw.get("fluency", 0)  # 流利度
    integrity = raw.get("integrity", 0)  # 完整度

    # 音素级详情
    word_details = []
    if "speechcheck" in raw:
        for word_info in raw["speechcheck"]:
            word_details.append({
                "word": word_info.get("word", ""),
                "score": word_info.get("score", 0),
                "pron": word_info.get("pron", 0),
                "error": word_info.get("error", ""),
            })

    # 生成评价建议
    suggestion = _generate_suggestion(overall, pron, fluency, integrity)

    return {
        "overall": overall,
        "pronunciation": pron,
        "fluency": fluency,
        "integrity": integrity,
        "word_details": word_details,
        "suggestion": suggestion,
        "text": text,
    }


def _generate_suggestion(overall: int, pron: int, fluency: int, integrity: int) -> str:
    """根据评分生成个性化建议。"""
    if overall >= 90:
        return "太棒了！你的发音非常标准，继续保持！"
    elif overall >= 80:
        return "很好！发音整体不错，可以再多练习一些细节。"
    elif overall >= 70:
        return "不错的尝试！注意以下几个方面会更好。"
    elif overall >= 60:
        return "继续加油！多听多模仿，你会越来越好的。"
    else:
        return "别灰心，每个人都是从零开始的。建议先从单个单词开始练习。"


def _parse_error_code(error_code: str) -> dict:
    """解析错误码。"""
    error_messages = {
        "101": "缺少必要的应用ID参数",
        "102": "不支持的语言类型",
        "103": "文本长度过长，不超过180字节",
        "104": "不支持的评测类型",
        "105": "音频文件格式错误",
        "106": "音频采样率错误，应为16K",
        "108": "音频文件过大",
        "109": "音频时长过长",
        "111": "应用ID无效",
        "112": "请求处理失败",
        "113": "查询失败",
        "201": "解密失败",
        "202": "签名检验失败",
        "203": "访问IP地址不在可访问IP列表",
        "204": "请求的接口与选择的接口不一致",
        "205": "请求的接口与选择的接口不一致",
        "206": "语音解密失败",
        "207": "语音识别失败",
        "208": "请求音频文件过小",
        "301": "辞典查询失败",
        "302": "翻译查询失败",
        "303": "服务端错误",
        "401": "账户欠费",
        "411": "访问频率受限，请稍后再试",
        "412": "长请求过于频繁，请稍后再试",
    }
    msg = error_messages.get(error_code, f"未知错误: {error_code}")
    return {"error": msg}


def _mock_evaluation(text: str) -> dict:
    """开发/测试用的模拟评测结果。"""
    import random
    overall = random.randint(60, 95)
    return {
        "overall": overall,
        "pronunciation": random.randint(55, 98),
        "fluency": random.randint(50, 95),
        "integrity": random.randint(60, 100),
        "word_details": [],
        "suggestion": _generate_suggestion(overall, overall, overall, overall),
        "text": text,
        "mock": True,
    }
