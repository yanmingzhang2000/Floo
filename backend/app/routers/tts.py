"""TTS 语音合成 API。

提供文本转语音接口，支持中英文朗读。
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.tts_service import text_to_speech

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    lang_type: str = "0"  # 0=英文，1=中文


class TTSResponse(BaseModel):
    audio: str
    format: str = "wav"


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(req: TTSRequest):
    """将文本转换为语音。"""
    if not req.text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    
    log.debug("收到 TTS 请求: text=%s, lang=%s", req.text[:20], req.lang_type)
    
    result = await text_to_speech(req.text, req.lang_type)
    
    if "error" in result:
        log.debug("TTS 合成失败: %s", result["error"])
        raise HTTPException(status_code=500, detail=result["error"])
    
    return TTSResponse(**result)
