"""
词汇收藏夹接口 - 支持收藏/取消收藏/获取收藏列表/检查是否已收藏。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserFavoriteWord

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/favorites", tags=["favorites"])


class FavoriteAddRequest(BaseModel):
    user_id: int
    word: str
    phonetic: str | None = None
    meaning: str | None = None
    source: str | None = None
    source_content_id: int | None = None


@router.post("/add")
def add_favorite(payload: FavoriteAddRequest, db: Session = Depends(get_db)):
    """收藏单词。"""
    # 检查是否已收藏
    existing = (
        db.query(UserFavoriteWord)
        .filter(
            UserFavoriteWord.user_id == payload.user_id,
            UserFavoriteWord.word == payload.word.lower()
        )
        .first()
    )
    if existing:
        log.debug("用户 %s 已收藏单词 %s", payload.user_id, payload.word)
        return {"success": True, "message": "已收藏", "id": existing.id}

    fav = UserFavoriteWord(
        user_id=payload.user_id,
        word=payload.word.lower(),
        phonetic=payload.phonetic,
        meaning=payload.meaning,
        source=payload.source,
        source_content_id=payload.source_content_id,
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    log.info("用户 %s 收藏单词 %s id=%s", payload.user_id, payload.word, fav.id)
    return {"success": True, "message": "收藏成功", "id": fav.id}


@router.delete("/remove")
def remove_favorite(user_id: int, word: str, db: Session = Depends(get_db)):
    """取消收藏单词。"""
    fav = (
        db.query(UserFavoriteWord)
        .filter(
            UserFavoriteWord.user_id == user_id,
            UserFavoriteWord.word == word.lower()
        )
        .first()
    )
    if not fav:
        log.debug("用户 %s 未收藏单词 %s", user_id, word)
        raise HTTPException(404, "未收藏该单词")

    db.delete(fav)
    db.commit()
    log.info("用户 %s 取消收藏单词 %s", user_id, word)
    return {"success": True, "message": "已取消收藏"}


@router.get("/list")
def get_favorites(user_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """获取用户收藏词汇列表。"""
    favs = (
        db.query(UserFavoriteWord)
        .filter(UserFavoriteWord.user_id == user_id)
        .order_by(UserFavoriteWord.created_at.desc())
        .limit(limit)
        .all()
    )
    log.debug("用户 %s 收藏词汇数=%s", user_id, len(favs))
    return [
        {
            "id": f.id,
            "word": f.word,
            "phonetic": f.phonetic,
            "meaning": f.meaning,
            "source": f.source,
            "created_at": f.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for f in favs
    ]


@router.get("/check")
def check_favorite(user_id: int, word: str, db: Session = Depends(get_db)):
    """检查单词是否已收藏。"""
    fav = (
        db.query(UserFavoriteWord)
        .filter(
            UserFavoriteWord.user_id == user_id,
            UserFavoriteWord.word == word.lower()
        )
        .first()
    )
    return {"is_favorite": fav is not None, "id": fav.id if fav else None}
