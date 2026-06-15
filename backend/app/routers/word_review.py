"""
单词复习接口 - 支持间隔重复 + 连续正确隐藏。
选义模式：返回待复习单词 + 干扰项；默写模式：返回待复习单词。
"""
import logging
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserFavoriteWord, UserWordProgress

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/word-review", tags=["word-review"])

# 阶段间隔（天）：阶段 0-4
_STAGE_INTERVALS = [0, 1, 3, 7, 15]
# 连续正确 >= N → 临时隐藏 days 天
_CONSECUTIVE_THRESHOLD = 3
_CONSECUTIVE_HIDE_DAYS = 3


class WordReviewSubmitRequest(BaseModel):
    user_id: int
    word: str
    correct: bool
    accuracy: float = 100.0  # 默写模式用，选义模式默认 100


@router.get("/due")
def get_due_words(user_id: int, limit: int = 15, db: Session = Depends(get_db)):
    """返回待复习单词 + 选义干扰项。

    优先级：到期复习词 > 新词（无进度记录）> 随机补充。
    连续正确 >= 3 的词在隐藏期内不出现。
    """
    now = datetime.utcnow()

    # 拉取用户全部收藏词
    all_favs = (
        db.query(UserFavoriteWord)
        .filter(UserFavoriteWord.user_id == user_id)
        .order_by(UserFavoriteWord.created_at.desc())
        .all()
    )
    if not all_favs:
        log.debug("用户 %s 无收藏单词", user_id)
        return {"words": [], "distractors": []}

    fav_map = {f.word: f for f in all_favs}

    # 拉取已有进度记录
    progress_rows = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user_id)
        .all()
    )
    progress_map = {p.word: p for p in progress_rows}

    due_words = []
    new_words = []

    for fav in all_favs:
        prog = progress_map.get(fav.word)
        if not prog:
            # 新词：从未复习过
            new_words.append(fav)
            continue
        # 连续正确隐藏期检查
        if prog.consecutive_correct >= _CONSECUTIVE_THRESHOLD and prog.next_review_at and prog.next_review_at > now:
            log.debug("单词 %s 连续正确 %s 次，隐藏中，下次 %s", fav.word, prog.consecutive_correct, prog.next_review_at)
            continue
        # 到期检查
        if prog.next_review_at and prog.next_review_at <= now:
            due_words.append((fav, prog))

    # 排序：按 next_review_at 升序（最早到期的优先）
    due_words.sort(key=lambda x: x[1].next_review_at or now)

    # 组装结果：先到期词，再新词，凑够 limit
    result = []
    for fav, prog in due_words[:limit]:
        result.append(_word_to_dict(fav, prog))
    if len(result) < limit:
        for fav in new_words[:limit - len(result)]:
            result.append(_word_to_dict(fav, None))
    # 不够就随机补充
    if len(result) < limit:
        used = {w["word"] for w in result}
        extras = [f for f in all_favs if f.word not in used]
        random.shuffle(extras)
        for fav in extras[:limit - len(result)]:
            prog = progress_map.get(fav.word)
            result.append(_word_to_dict(fav, prog))

    # 干扰项：从所有收藏词中随机抽（排除当前轮的词），取 meaning 非空的
    current_words = {w["word"] for w in result}
    distractor_pool = [f for f in all_favs if f.word not in current_words and f.meaning]
    random.shuffle(distractor_pool)
    distractors = [
        {"word": f.word, "meaning": f.meaning}
        for f in distractor_pool[:30]  # 返回足够多供前端随机抽
    ]

    log.debug("用户 %s 复习词数=%s 干扰项数=%s", user_id, len(result), len(distractors))
    return {"words": result, "distractors": distractors}


@router.post("/submit")
def submit_word_review(payload: WordReviewSubmitRequest, db: Session = Depends(get_db)):
    """提交单词复习结果，更新记忆状态。

    正确：consecutive_correct++，阶段推进
    错误：consecutive_correct=0，阶段重置
    consecutive_correct >= 3：短期隐藏 3 天
    """
    now = datetime.utcnow()
    word = payload.word.lower()

    prog = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == payload.user_id, UserWordProgress.word == word)
        .first()
    )
    if not prog:
        prog = UserWordProgress(user_id=payload.user_id, word=word)
        db.add(prog)

    if payload.correct:
        prog.consecutive_correct += 1
        prog.total_correct += 1
        # 阶段推进：连续正确且 accuracy >= 80 才推进
        if payload.accuracy >= 80 and prog.current_stage < len(_STAGE_INTERVALS) - 1:
            prog.current_stage += 1
    else:
        prog.consecutive_correct = 0
        prog.total_wrong += 1
        # 错误重置到阶段 0
        prog.current_stage = 0

    prog.last_accuracy = payload.accuracy
    prog.updated_at = now

    # 计算下次复习时间
    if prog.consecutive_correct >= _CONSECUTIVE_THRESHOLD:
        # 连续正确达标：短期隐藏
        prog.next_review_at = now + timedelta(days=_CONSECUTIVE_HIDE_DAYS)
        log.debug("单词 %s 连续正确 %s 次，隐藏 %s 天", word, prog.consecutive_correct, _CONSECUTIVE_HIDE_DAYS)
    else:
        interval = _STAGE_INTERVALS[prog.current_stage]
        prog.next_review_at = now + timedelta(days=interval)

    db.commit()
    log.debug(
        "用户 %s 单词 %s correct=%s stage=%s consecutive=%s next=%s",
        payload.user_id, word, payload.correct, prog.current_stage,
        prog.consecutive_correct, prog.next_review_at,
    )
    return {
        "success": True,
        "consecutive_correct": prog.consecutive_correct,
        "current_stage": prog.current_stage,
        "next_review_at": prog.next_review_at.isoformat() if prog.next_review_at else None,
    }


def _word_to_dict(fav: UserFavoriteWord, prog: UserWordProgress | None) -> dict:
    return {
        "word": fav.word,
        "phonetic": fav.phonetic,
        "meaning": fav.meaning,
        "consecutive_correct": prog.consecutive_correct if prog else 0,
        "current_stage": prog.current_stage if prog else 0,
        "total_correct": prog.total_correct if prog else 0,
        "total_wrong": prog.total_wrong if prog else 0,
    }
