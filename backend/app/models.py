"""
Floo! (飞路一下) 数据库模型 - 11 表设计

业务集群划分：
- 集群一：用户与偏好设定（user_main, user_learning_preference）
- 集群二：内容生产（learning_contents）
- 集群三：学习行为与记忆追踪（user_memory_progress, user_checkin_records,
         user_dictation_history, user_weekly_summary）
- 集群四：游戏化激励（user_point_account, point_log_history）
- 集群五：积分商城（character, user_collection）
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ============== 业务集群一：用户与偏好设定 ==============

class UserMain(Base):
    """用户主表 - 存储账户核心凭证及基础注册信息。"""
    __tablename__ = "user_main"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    nickname = Column(String(64), nullable=False, default="Floo学习者")
    email = Column(String(128), unique=True, nullable=True, index=True)
    avatar_url = Column(String(512), nullable=True)
    register_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    preference = relationship("UserLearningPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    point_account = relationship("UserPointAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memory_progress = relationship("UserMemoryProgress", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("UserCheckinRecord", back_populates="user", cascade="all, delete-orphan")
    dictations = relationship("UserDictationHistory", back_populates="user", cascade="all, delete-orphan")
    weekly_summaries = relationship("UserWeeklySummary", back_populates="user", cascade="all, delete-orphan")
    custom_contents = relationship("LearningContent", back_populates="creator", foreign_keys="LearningContent.user_id")
    collections = relationship("UserCollection", back_populates="user", cascade="all, delete-orphan")
    learned_contents = relationship("UserLearnedContent", back_populates="user", cascade="all, delete-orphan")


class UserLearningPreference(Base):
    """用户学习偏好表 - 难度级别和主题选择，AI 生成内容时的 Prompt 参数来源。"""
    __tablename__ = "user_learning_preference"

    preference_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    # AI 生成内容时必须读取这两个字段作为 Prompt 输入参数
    difficulty_level = Column(String(16), default="medium", nullable=False)
    theme_type = Column(String(32), default="daily_life", nullable=False)
    daily_goal_count = Column(Integer, default=5, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserMain", back_populates="preference")


# ============== 业务集群二：内容生产与个性化 ==============

class LearningContent(Base):
    """
    学习内容库表 - 所有学习行为的唯一锚点。
    creator_type=0 为 AI 每日推送（user_id 为 NULL），creator_type=1 为用户自定义。
    """
    __tablename__ = "learning_contents"

    content_id = Column(Integer, primary_key=True, autoincrement=True)
    # 0=AI生成, 1=用户自定义
    creator_type = Column(Integer, default=0, nullable=False)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=True)
    difficulty_level = Column(String(16), nullable=False)
    theme_type = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    translation = Column(Text, nullable=True)
    # JSON 字符串存储，保持 MySQL 兼容性
    phonetic = Column(Text, nullable=True)
    key_words = Column(Text, nullable=True)
    audio_url = Column(String(512), nullable=True)
    content_type = Column(String(16), default="article", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    creator = relationship("UserMain", back_populates="custom_contents", foreign_keys=[user_id])
    memory_records = relationship("UserMemoryProgress", back_populates="content", cascade="all, delete-orphan")
    dictation_records = relationship("UserDictationHistory", back_populates="content")


# ============== 业务集群三：学习行为与记忆追踪 ==============

class UserMemoryProgress(Base):
    """
    用户记忆进度追踪表 - 艾宾浩斯记忆曲线中央调度盘。
    系统每天通过 next_review_at <= 当前时间 捞出该用户今天该复习的内容。
    """
    __tablename__ = "user_memory_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_user_content"),
        # 复习任务捞取的核心查询索引
        Index("idx_review_schedule", "user_id", "next_review_at"),
    )

    progress_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("learning_contents.content_id", ondelete="CASCADE"), nullable=False, index=True)
    # 0=新学, 1-7 对应艾宾浩斯间隔（1/2/4/7/15/30/60天）
    review_stage = Column(Integer, default=0, nullable=False)
    last_review_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True, index=True)
    total_review_count = Column(Integer, default=0, nullable=False)
    # 每次默写完成后覆盖更新此字段
    last_accuracy = Column(Numeric(5, 2), default=0.00, nullable=False)
    is_mastered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserMain", back_populates="memory_progress")
    content = relationship("LearningContent", back_populates="memory_records")


class UserCheckinRecord(Base):
    """每日学习打卡表 - 前端日历热力图的直接数据源。"""
    __tablename__ = "user_checkin_records"
    __table_args__ = (
        UniqueConstraint("user_id", "checkin_date", name="uq_user_checkin_date"),
        Index("idx_checkin_user_week", "user_id", "year_week"),
    )

    checkin_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    checkin_date = Column(Date, nullable=False, index=True)
    # 格式 YYYYWW，供周报聚合扫描
    year_week = Column(String(6), nullable=False)
    completed_count = Column(Integer, default=0, nullable=False)
    earned_points = Column(Integer, default=10, nullable=False)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserMain", back_populates="checkins")


class UserDictationHistory(Base):
    """
    用户默写历史流水表 - 增量记录，永不覆盖。
    周复习时从此表捞本周 accuracy_rate 最低的 content_id 推给用户复习。
    """
    __tablename__ = "user_dictation_history"
    __table_args__ = (
        Index("idx_dictation_user_content", "user_id", "content_id"),
        Index("idx_dictation_user_week", "user_id", "year_week"),
    )

    dictation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("learning_contents.content_id", ondelete="SET NULL"), nullable=True, index=True)
    year_week = Column(String(6), nullable=False)
    original_text = Column(Text, nullable=False)
    user_input = Column(Text, nullable=False)
    accuracy_rate = Column(Numeric(5, 2), default=0.00, nullable=False)
    time_spent_seconds = Column(Integer, nullable=True)
    # JSON 字符串：AI 详细批改结果
    ai_feedback = Column(Text, nullable=True)
    # JSON 字符串：高频错词列表，供错词分析
    error_words = Column(Text, nullable=True)
    earned_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("UserMain", back_populates="dictations")
    content = relationship("LearningContent", back_populates="dictation_records")


class UserWeeklySummary(Base):
    """
    每周学习数据统计表 - 周报和周复习的判定基准。
    weekly_review_status=1 时，系统从 user_dictation_history 捞本周低正确率内容推送复习。
    """
    __tablename__ = "user_weekly_summary"
    __table_args__ = (
        UniqueConstraint("user_id", "year_week", name="uq_user_week_summary"),
    )

    summary_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    year_week = Column(String(6), nullable=False, index=True)
    total_checkin_days = Column(Integer, default=0, nullable=False)
    total_learned_count = Column(Integer, default=0, nullable=False)
    avg_accuracy_rate = Column(Numeric(5, 2), default=0.00, nullable=False)
    total_earned_points = Column(Integer, default=0, nullable=False)
    # 0=未开始, 1=进行中, 2=已完成
    weekly_review_status = Column(Integer, default=0, nullable=False)
    review_started_at = Column(DateTime, nullable=True)
    review_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserMain", back_populates="weekly_summaries")


# ============== 业务集群四：游戏化激励 ==============

class DailyGenerationLimit(Base):
    """
    每日内容生成次数限制表 - 每用户每天最多生成3次。
    limit_type 区分 AI 生成（ai）和自定义内容（custom），两者独立计数。
    """
    __tablename__ = "daily_generation_limit"
    __table_args__ = (
        UniqueConstraint("user_id", "limit_date", "limit_type", name="uq_user_date_limit_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    limit_date = Column(Date, nullable=False, index=True)
    limit_type = Column(String(16), default="ai", nullable=False)
    generation_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserFavoriteWord(Base):
    """用户收藏词汇表 - 用户可收藏任意单词。"""
    __tablename__ = "user_favorite_words"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_user_favorite_word"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(128), nullable=False, index=True)
    phonetic = Column(String(128), nullable=True)
    meaning = Column(String(512), nullable=True)
    source = Column(String(32), nullable=True)  # 从哪里收藏的：daily/dictation/review
    source_content_id = Column(Integer, nullable=True)  # 来源内容ID
    is_mastered = Column(Boolean, default=False, nullable=False)  # 是否已掌握
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserWordProgress(Base):
    """单词级记忆追踪表 - 支持间隔重复和连续正确隐藏。
    和 user_favorite_words 配合：只有收藏的单词才进入复习池。"""
    __tablename__ = "user_word_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_user_word_progress"),
        Index("idx_word_review_schedule", "user_id", "next_review_at"),
    )

    progress_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(128), nullable=False, index=True)
    consecutive_correct = Column(Integer, default=0, nullable=False)  # 连续正确次数，>=3 短期不出现
    current_stage = Column(Integer, default=0, nullable=False)  # 复习阶段 0-4
    next_review_at = Column(DateTime, nullable=True)  # 下次复习时间
    total_correct = Column(Integer, default=0, nullable=False)
    total_wrong = Column(Integer, default=0, nullable=False)
    last_accuracy = Column(Numeric(5, 2), default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPointAccount(Base):
    """用户积分账户表 - 全局积分资产，余额变更必须同步写 point_log_history 流水。"""
    __tablename__ = "user_point_account"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_earned_points = Column(Integer, default=0, nullable=False)
    available_points = Column(Integer, default=0, nullable=False)
    total_consumed_points = Column(Integer, default=0, nullable=False)
    current_streak_days = Column(Integer, default=0, nullable=False)
    max_streak_days = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserMain", back_populates="point_account")
    transactions = relationship("PointLogHistory", back_populates="account", cascade="all, delete-orphan")


class PointLogHistory(Base):
    """积分流水表 - 任何余额变动都必须在此留记录，用于对账和兑换溯源。"""
    __tablename__ = "point_log_history"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("user_point_account.account_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    # 正数=获得，负数=消费
    change_amount = Column(Integer, nullable=False)
    # checkin / dictation / redeem / bonus
    change_type = Column(String(32), nullable=False)
    reference_id = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    account = relationship("UserPointAccount", back_populates="transactions")


# ============== 业务集群五：积分商城 ==============

class Character(Base):
    """角色表 - 积分商城盲盒角色，每个角色对应一个好词。"""
    __tablename__ = "character"

    character_id = Column(Integer, primary_key=True, autoincrement=True)
    # 角色名称（英文好词）
    name = Column(String(64), unique=True, nullable=False, index=True)
    # 中文含义
    meaning = Column(String(128), nullable=False)
    # 图片URL
    image_url = Column(String(512), nullable=True)
    # 稀有度：common/rare/legendary
    rarity = Column(String(16), nullable=False, default="common")
    # 角色描述
    description = Column(String(512), nullable=True)
    # 抽取概率（万分比）
    weight = Column(Integer, nullable=False, default=7000)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    collections = relationship("UserCollection", back_populates="character")


class UserLearnedContent(Base):
    """用户已学内容表 - 记录用户标记为「已学过」的文章。"""
    __tablename__ = "user_learned_content"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_user_learned_content"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("learning_contents.content_id", ondelete="CASCADE"), nullable=False, index=True)
    learned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserMain", back_populates="learned_contents")
    content = relationship("LearningContent")


class UserOpenedContent(Base):
    """用户已打开内容表 - 记录用户首次打开某篇内容的时间。

    Why 独立建表而不复用 UserLearnedContent：
    「打开」和「学完」是两个不同的语义阶段。打开 → 正在学习；学完 → 已归档。
    两者都缺失 → 内容从未进入「在读」流程，不应出现在读书页。
    """
    __tablename__ = "user_opened_content"
    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_user_opened_content"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("learning_contents.content_id", ondelete="CASCADE"), nullable=False, index=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserMain")
    content = relationship("LearningContent")


class UserCollection(Base):
    """用户收藏表 - 记录用户抽到的角色。"""
    __tablename__ = "user_collection"
    __table_args__ = (
        UniqueConstraint("user_id", "character_id", name="uq_user_character"),
    )

    collection_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    character_id = Column(Integer, ForeignKey("character.character_id", ondelete="CASCADE"), nullable=False, index=True)
    # 抽到的数量（重复角色累加）
    count = Column(Integer, default=1, nullable=False)
    # 第一次获得时间
    obtained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # 最近一次获得时间
    last_obtained_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserMain", back_populates="collections")
    character = relationship("Character", back_populates="collections")


# ============== 业务集群六：书籍精读（白名单授权） ==============
#
# 为什么单独建 4 张表而不是复用 learning_contents：
#   - learning_contents 是"孤立"内容锚点，没有目录/顺序/授权语义。
#   - 书籍需要「章节顺序 + 分段顺序 + 用户可访问性」三层结构。
# 所以拆成：
#   1. BookSeries：一本书聚合根
#   2. BookChapter：章节 → 对应「整章」学习内容记录（learning_contents.content_id）
#   3. BookChapterSegment：章节分段 → 对应「分段」学习内容记录（learning_contents.content_id）
#   4. UserBookAccess：白名单授权，只有这里有记录的用户才能看见对应书

class BookSeries(Base):
    """书籍套装表 - 一本书对应一条记录，作为章节聚合根。

    source_url 用作幂等键：同一目录页 URL 只能导入一次，
    避免 admin 重复触发抓取产生重复数据。
    """
    __tablename__ = "book_series"

    series_id = Column(Integer, primary_key=True, autoincrement=True)
    # 英文原名，用于展示和检索
    name = Column(String(128), nullable=False)
    # 中文译名
    name_cn = Column(String(128), nullable=True)
    author = Column(String(128), nullable=True)
    # 来源站点标识（tingroom / gutenberg / manual），用于扩展多站点
    source_site = Column(String(64), nullable=True)
    # 目录页 URL，作为幂等键
    source_url = Column(String(512), nullable=True, unique=True)
    cover_url = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    total_chapters = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BookChapter(Base):
    """章节表 - 每章一条，指向 learning_contents 里的整章记录。

    order_no 唯一：0=Introduction，1=Chapter 1，2=Chapter 2 …
    content_id 指向「整章」内容；「分段」内容通过 BookChapterSegment 关联。
    """
    __tablename__ = "book_chapter"
    __table_args__ = (
        UniqueConstraint("series_id", "order_no", name="uq_series_chapter_order"),
        Index("idx_chapter_series", "series_id", "order_no"),
    )

    chapter_id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey("book_series.series_id", ondelete="CASCADE"), nullable=False, index=True)
    order_no = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    source_url = Column(String(512), nullable=False)
    # 整章模式对应的 learning_contents 记录
    content_id = Column(Integer, ForeignKey("learning_contents.content_id"), nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BookChapterSegment(Base):
    """章节分段表 - 每段 400-500 词，供分段模式使用。

    整章 vs 分段模式：
      - 整章：读 BookChapter.content_id 一条记录
      - 分段：按 order_no 遍历本表，每段一条 learning_contents 记录
    这样两种模式共用 learning_contents 底层，词典/朗读/默写全部继承。
    """
    __tablename__ = "book_chapter_segment"
    __table_args__ = (
        UniqueConstraint("chapter_id", "order_no", name="uq_chapter_segment_order"),
        Index("idx_segment_chapter", "chapter_id", "order_no"),
    )

    segment_id = Column(Integer, primary_key=True, autoincrement=True)
    chapter_id = Column(Integer, ForeignKey("book_chapter.chapter_id", ondelete="CASCADE"), nullable=False, index=True)
    order_no = Column(Integer, nullable=False)
    content_id = Column(Integer, ForeignKey("learning_contents.content_id"), nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    # 该段在整章 content_text 中的字符起止位置（含起、不含止），
    # detail 页据此在整章文本上画分割线。
    # 允许 null 兼容旧数据（早期导入未记录偏移）。
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)


class UserBookAccess(Base):
    """用户书籍授权表 - 白名单闸门。

    为什么单独建表而不是加字段：
      - 一个用户可能被授权多本书（未来扩展）
      - 授权可撤销（is_active=False），审计需要 granted_by / granted_at
      - 判断可访问性只需一次 index 查询，比在多张表加 join 简单
    """
    __tablename__ = "user_book_access"
    __table_args__ = (
        UniqueConstraint("user_id", "series_id", name="uq_user_book_access"),
        Index("idx_book_access_user", "user_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user_main.user_id", ondelete="CASCADE"), nullable=False, index=True)
    series_id = Column(Integer, ForeignKey("book_series.series_id", ondelete="CASCADE"), nullable=False, index=True)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # admin 标识（"admin" 或运营者账号），审计用
    granted_by = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)