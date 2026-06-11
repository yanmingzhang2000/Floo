"""语音评测 API。

提供发音评测接口，前端录音后发送音频到此接口进行评分。
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.speech_evaluator import evaluate_pronunciation

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/speech", tags=["speech"])


class EvaluateRequest(BaseModel):
    audio: str        # base64 编码的音频
    text: str         # 要评测的文本
    lang_type: str = "en"  # en 或 zh_cn


class EvaluateResponse(BaseModel):
    overall: int
    pronunciation: int
    fluency: int
    integrity: int
    suggestion: str
    word_details: list = []


@router.post("/evaluate", response_model=EvaluateResponse)
async def speech_evaluate(req: EvaluateRequest):
    """评测用户发音。"""
    if not req.audio:
        raise HTTPException(status_code=400, detail="音频数据不能为空")
    if not req.text:
        raise HTTPException(status_code=400, detail="评测文本不能为空")

    log.debug("收到语音评测请求: text=%s, lang=%s", req.text, req.lang_type)

    result = await evaluate_pronunciation(req.audio, req.text, req.lang_type)

    if "error" in result:
        log.debug("语音评测失败: %s", result["error"])
        raise HTTPException(status_code=500, detail=result["error"])

    return EvaluateResponse(**result)
