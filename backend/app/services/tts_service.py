"""TTS 语音合成服务。

使用有道智云 TTS 接口将文本转换为语音。
"""
import hashlib
import hmac
import time
import random
import string
import base64
import logging
import httpx

from app.config import settings

log = logging.getLogger(__name__)

YOUDAO_TTS_URL = "https://openapi.youdao.com/ttsapi"


def _generate_salt() -> str:
    """生成随机 salt。"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))


def _sign(text: str, salt: str, curtime: str) -> str:
    """生成有道 API 签名。"""
    sign_str = settings.YOUDAO_APP_ID + text + salt + curtime + settings.YOUDAO_APP_SECRET
    return hashlib.sha256(sign_str.encode()).hexdigest()


async def text_to_speech(text: str, lang_type: str = "0") -> dict:
    """调用有道智云 TTS 接口。
    
    Args:
        text: 要合成的文本
        lang_type: 语言类型，0=英文，1=中文
    
    Returns:
        {"audio": "base64编码的音频", "format": "wav"} 或 {"error": "错误信息"}
    """
    if not settings.YOUDAO_APP_ID:
        log.debug("YOUDAO_APP_ID 未配置，无法调用 TTS")
        return {"error": "TTS 服务未配置"}
    
    if not text.strip():
        return {"error": "文本不能为空"}
    
    # 截断过长文本
    if len(text) > 500:
        text = text[:500]
        log.debug("TTS 文本过长，截断至 500 字符")
    
    salt = _generate_salt()
    curtime = str(int(time.time() * 1000))
    sign = _sign(text, salt, curtime)
    
    data = {
        "q": text,
        "langType": lang_type,
        "appKey": settings.YOUDAO_APP_ID,
        "salt": salt,
        "sign": sign,
        "signType": "v3",
        "curtime": curtime,
        "voice": "0",  # 0=女声
        "speed": "1.0",  # 语速
    }
    
    log.debug("调用有道 TTS: text=%s, lang=%s", text[:20], lang_type)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(YOUDAO_TTS_URL, data=data)
            resp.raise_for_status()
            result = resp.json()
            
            if "errorCode" in result and result["errorCode"] != "0":
                log.debug("有道 TTS 返回错误: %s", result["errorCode"])
                return {"error": f"TTS 失败: {result['errorCode']}"}
            
            audio = result.get("audio", "")
            if audio:
                log.debug("TTS 成功，音频长度: %d", len(audio))
                return {"audio": audio, "format": "wav"}
            else:
                return {"error": "TTS 返回空音频"}
                
    except Exception as e:
        log.debug("TTS 请求异常: %s", e)
        return {"error": f"请求 TTS 服务失败: {str(e)}"}
