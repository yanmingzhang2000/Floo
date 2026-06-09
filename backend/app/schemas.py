"""
Floo! API 请求/响应模型 - 对齐新 9 表设计。

保持部分旧接口命名以兼容现有前端，内部映射到新表结构。
"""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============== 用户相关 ==============

class UserRegisterRequest(BaseModel):
    """用户注册请求。"""
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    nickname: str = Field(default="Floo学习者", max_length=64)
    email: Optional[str] = None


class UserLoginRequest(BaseModel):
    """用户登录请求。"""
    username: str
    password: str


class UserOut(BaseModel):
    """用户基本信息输出。"""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    nickname: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferenceOut(BaseModel):
    """用户学习偏好输出。"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    difficulty_level: str
    theme_type: str
    daily_goal_count: int

    @property
    def daily_goal_minutes(self) -> int:
        """前端使用daily_goal_minutes字段名。"""
        return self.daily_goal_count


class UserPreferenceUpdate(BaseModel):
    """更新学习偏好。"""
    model_config = ConfigDict(populate_by_name=True)

    difficulty_level: Optional[str] = None
    theme_type: Optional[str] = None
    daily_goal_count: Optional[int] = Field(None, alias="daily_goal_minutes")


# ============== 学习内容相关 ==============

class LearningContentOut(BaseModel):
    """
    学习内容输出 - 兼容旧前端的 DailyContentOut。
    前端仍用 content_date/article 字段，内部映射到 created_at/content_text。
    """
    model_config = ConfigDict(from_attributes=True)

    id: int  # 映射 content_id
    content_date: str  # 映射 created_at 转 date 字符串
    title: str
    article: str  # 映射 content_text
    translation: Optional[str] = None
    audio_url: Optional[str] = None
    difficulty_level: str
    theme_type: str
    # key_words 从 JSON 字符串解析后返回
    words: list[dict[str, Any]] = []  # 临时用 dict，后续可拆单独表
    content_type: str = "article"  # overview=今日总览, article=详细文章


# 合法 theme 枚举值
THEME_OPTIONS = ("ai_tech", "product_tech", "business", "daily_news", "self_growth", "all_random")


class GenerateContentRequest(BaseModel):
    """生成学习内容请求。theme 对应用户偏好，同 theme 当日共享内容。"""
    user_id: int = 1
    theme_override: Optional[str] = None  # 临时覆盖主题，调试用
    force: bool = False  # 强制重新生成，忽略今日已有内容


class TodayContentListResponse(BaseModel):
    """今日完整学习内容列表，前端根据 daily_goal_minutes 决定展示几条。"""
    theme: str
    daily_goal_minutes: int
    contents: list["LearningContentOut"]


class GenerateContentResult(BaseModel):
    """生成结果。content_id 保留第一篇 ID 供向后兼容，content_ids 包含全部。"""
    content_id: int
    content_ids: list[int]
    count: int
    message: str


# ============== 默写相关 ==============

class DictationSubmitRequest(BaseModel):
    """提交默写请求。"""
    user_id: int = 1
    content_id: int
    user_input: str


class DictationFeedback(BaseModel):
    """AI 批改反馈。"""
    score: int
    summary: str
    diffs: list[dict[str, Any]] = []
    suggestions: list[str] = []


class DictationSubmitResponse(BaseModel):
    """默写提交响应。"""
    dictation_id: int
    accuracy_rate: float
    feedback: DictationFeedback
    earned_points: int
    # 记忆进度更新结果
    next_review_at: Optional[datetime] = None
    review_stage: int


class DictationHistoryOut(BaseModel):
    """默写历史记录。"""
    model_config = ConfigDict(from_attributes=True)

    dictation_id: int
    content_id: Optional[int]
    accuracy_rate: float
    time_spent_seconds: Optional[int]
    earned_points: int
    created_at: datetime


# ============== 打卡相关 ==============

class CheckinRequest(BaseModel):
    """打卡请求。"""
    user_id: int = 1
    note: Optional[str] = None


class CheckinOut(BaseModel):
    """打卡记录输出。"""
    model_config = ConfigDict(from_attributes=True)

    checkin_id: int
    checkin_date: date
    completed_count: int
    earned_points: int
    note: Optional[str] = None


class CheckinResponse(BaseModel):
    """打卡响应 - 包含积分账户更新。"""
    checkin: CheckinOut
    available_points: int
    current_streak_days: int


class CheckinCalendarOut(BaseModel):
    """打卡日历数据。"""
    user_id: int
    year: int
    month: int
    checked_dates: list[date]
    available_points: int
    current_streak_days: int


# ============== 记忆复习相关 ==============

class ReviewTaskOut(BaseModel):
    """待复习任务。"""
    content_id: int
    title: str
    review_stage: int
    last_accuracy: float
    next_review_at: datetime


class ReviewListResponse(BaseModel):
    """今日复习列表。"""
    user_id: int
    total_count: int
    tasks: list[ReviewTaskOut]


class MemoryProgressOut(BaseModel):
    """单条内容的记忆进度。"""
    content_id: int
    title: str
    review_stage: int
    last_accuracy: float
    next_review_at: Optional[datetime] = None
    is_mastered: bool
    total_review_count: int


class MemoryProgressListResponse(BaseModel):
    """用户全部记忆进度列表。"""
    user_id: int
    total_count: int
    mastered_count: int
    items: list[MemoryProgressOut]


# ============== 周报相关 ==============

class WeeklySummaryOut(BaseModel):
    """每周学习总结输出。"""
    model_config = ConfigDict(from_attributes=True)

    year_week: str
    total_checkin_days: int
    total_learned_count: int
    avg_accuracy_rate: float
    total_earned_points: int
    weekly_review_status: int


# ============== 积分相关 ==============

class PointAccountOut(BaseModel):
    """积分账户输出。"""
    model_config = ConfigDict(from_attributes=True)

    total_earned_points: int
    available_points: int
    total_consumed_points: int
    current_streak_days: int
    max_streak_days: int


class PointTransactionOut(BaseModel):
    """积分流水输出。"""
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    change_amount: int
    change_type: str
    description: Optional[str]
    balance_after: int
    created_at: datetime