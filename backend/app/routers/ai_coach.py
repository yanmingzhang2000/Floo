"""AI陪练 API。

提供语音对话练习接口，支持中英混合对话。
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_coach_service import process_audio, chat_with_ai, synthesize_speech

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-coach", tags=["ai-coach"])


class TranscribeRequest(BaseModel):
    audio: str        # base64 编码的音频
    format: str = "mp3"  # 音频格式


class TranscribeResponse(BaseModel):
    success: bool
    text: str = ""
    lang: str = ""
    error: str = ""


class ChatRequest(BaseModel):
    text: str         # 用户输入文本
    lang: str = "en"  # 语言：en 或 zh
    history: list = []  # 对话历史


class ChatResponse(BaseModel):
    success: bool
    reply: str = ""
    lang: str = ""
    error: str = ""


class TTSRequest(BaseModel):
    text: str         # 要转换的文本
    lang: str = "en"  # 语言：en 或 zh


class TTSResponse(BaseModel):
    success: bool
    audio: str = ""   # base64 编码的音频
    error: str = ""


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(req: TranscribeRequest):
    """语音转文字 + 语言检测。"""
    if not req.audio:
        raise HTTPException(status_code=400, detail="音频数据不能为空")

    log.debug("收到语音转文字请求: format=%s", req.format)

    result = await process_audio(req.audio, req.format)

    if not result.get("success"):
        log.debug("语音转文字失败: %s", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))

    return TranscribeResponse(**result)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """聊天接口 - 中英翻译 / 英语问答。"""
    if not req.text:
        raise HTTPException(status_code=400, detail="文本不能为空")

    log.debug("收到聊天请求: text=%s, lang=%s", req.text[:50], req.lang)

    result = await chat_with_ai(req.text, req.lang, req.history)

    if not result.get("success"):
        log.debug("聊天失败: %s", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))

    return ChatResponse(**result)


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(req: TTSRequest):
    """文字转语音。"""
    if not req.text:
        raise HTTPException(status_code=400, detail="文本不能为空")

    log.debug("收到TTS请求: text=%s, lang=%s", req.text[:50], req.lang)

    result = await synthesize_speech(req.text, req.lang)

    if not result.get("success"):
        log.debug("TTS失败: %s", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))

    return TTSResponse(**result)
