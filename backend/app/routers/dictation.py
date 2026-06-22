"""
接口 2：默写提交与批改。

为什么积分计算放在 router 层：积分规则简单（正确率/10），
是业务编排逻辑而非数据存取，放 router 够用，复杂化后再抽 service。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import content_repo, dictation_repo, user_repo
from app.schemas import (
    DictationFeedback,
    DictationHistoryDetailOut,
    DictationHistoryOut,
    DictationSubmitRequest,
    DictationSubmitResponse,
)
from app.services.dictation_corrector import correct_dictation

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dictation", tags=["dictation"])


@router.post("/submit", response_model=DictationSubmitResponse)
async def submit_dictation(
    payload: DictationSubmitRequest,
    db: Session = Depends(get_db),
):
    """接收默写内容，调 AI 批改，更新记忆进度，发放积分。"""
    if not payload.user_input.strip():
        log.debug("user_input 为空，拒绝请求")
        raise HTTPException(400, "默写内容不能为空")

    user = user_repo.get_user(db, payload.user_id)
    if not user:
        log.debug("user_id=%s 不存在", payload.user_id)
        raise HTTPException(404, "用户不存在")

    content = content_repo.get_content_by_id(db, payload.content_id)
    if not content:
        log.debug("content_id=%s 不存在", payload.content_id)
        raise HTTPException(404, "学习内容不存在")

    # 调 AI 批改（LLM 不可用时自动降级到本地 diff）
    feedback = await correct_dictation(content.content_text, payload.user_input)
    score = int(feedback.get("score", 0))
    # 最低保底 50 分，用户练习信心重要
    score = max(50, score)
    accuracy_rate = float(score)

    # 积分规则：正确率 / 10 向下取整，上限 10 分
    earned = min(10, max(0, score // 10))
    log.debug("批改完成 score=%s earned_points=%s", score, earned)

    # 写默写流水记录
    record = dictation_repo.create_dictation(
        db=db,
        user_id=user.user_id,
        content_id=content.content_id,
        original_text=content.content_text,
        user_input=payload.user_input,
        accuracy_rate=accuracy_rate,
        feedback=feedback,
        earned_points=earned,
    )

    # 覆盖更新记忆进度（艾宾浩斯阶段 + 下次复习时间）
    progress = dictation_repo.update_memory_progress(
        db=db,
        user_id=user.user_id,
        content_id=content.content_id,
        accuracy_rate=accuracy_rate,
    )

    # 发放积分
    if earned > 0:
        account = user_repo.get_point_account(db, user.user_id)
        if account:
            user_repo.add_points(
                db=db,
                account=account,
                amount=earned,
                change_type="dictation",
                reference_id=record.dictation_id,
                description=f"默写得分 {score}",
            )
        else:
            log.debug("user_id=%s 无积分账户，跳过加分", user.user_id)

    db.commit()
    db.refresh(record)
    db.refresh(progress)

    return DictationSubmitResponse(
        dictation_id=record.dictation_id,
        accuracy_rate=float(record.accuracy_rate),
        feedback=DictationFeedback(**feedback),
        earned_points=earned,
        next_review_at=progress.next_review_at,
        review_stage=progress.review_stage,
    )


@router.get("/history", response_model=list[DictationHistoryOut])
def get_history(
    user_id: int = 1,
    limit: int = 1000,
    db: Session = Depends(get_db),
):
    """查询用户最近的默写记录，带上学习内容标题。"""
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在", user_id)
        raise HTTPException(404, "用户不存在")
    records = dictation_repo.list_user_dictations(db, user_id, limit=limit)

    # 批量查询学习内容标题
    content_ids = [r.content_id for r in records if r.content_id]
    titles = {}
    if content_ids:
        from app.models import LearningContent
        contents = db.query(LearningContent.content_id, LearningContent.title).filter(
            LearningContent.content_id.in_(content_ids)
        ).all()
        titles = {c.content_id: c.title for c in contents}

    # 构造输出，注入 content_title
    # 单条记录序列化失败不中断整个接口，跳过并记录日志
    out = []
    for r in records:
        try:
            item = DictationHistoryOut.model_validate(r)
            item.content_title = titles.get(r.content_id)
            out.append(item)
        except Exception as e:
            log.debug("跳过序列化失败的默写记录 dictation_id=%s: %s", r.dictation_id, e)

    log.debug("返回默写历史 user_id=%s count=%s", user_id, len(out))
    return out


@router.get("/history/{dictation_id}", response_model=DictationHistoryDetailOut)
def get_history_detail(
    dictation_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """查询单条默写记录详情，包含原文、用户输入和 AI 批改结果。"""
    from app.models import UserDictationHistory, LearningContent

    record = db.query(UserDictationHistory).filter(
        UserDictationHistory.dictation_id == dictation_id,
        UserDictationHistory.user_id == user_id,
    ).first()
    if not record:
        log.debug("dictation_id=%s user_id=%s 不存在", dictation_id, user_id)
        raise HTTPException(404, "记录不存在")

    # 查内容标题
    content_title = None
    if record.content_id:
        content = db.query(LearningContent.title).filter(
            LearningContent.content_id == record.content_id
        ).first()
        if content:
            content_title = content.title

    # 解析 JSON 字符串
    import json
    ai_feedback = None
    if record.ai_feedback:
        try:
            ai_feedback = DictationFeedback(**json.loads(record.ai_feedback))
        except Exception as e:
            log.debug("解析 ai_feedback 失败 dictation_id=%s: %s", dictation_id, e)

    error_words = []
    if record.error_words:
        try:
            error_words = json.loads(record.error_words)
        except Exception:
            pass

    return DictationHistoryDetailOut(
        dictation_id=record.dictation_id,
        content_id=record.content_id,
        content_title=content_title,
        original_text=record.original_text,
        user_input=record.user_input,
        accuracy_rate=float(record.accuracy_rate),
        time_spent_seconds=record.time_spent_seconds,
        earned_points=record.earned_points,
        ai_feedback=ai_feedback,
        error_words=error_words,
        created_at=record.created_at,
    )