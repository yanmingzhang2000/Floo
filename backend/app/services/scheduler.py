"""每日定时生成 AI 新闻的调度器。

为什么用 APScheduler 而不是 Railway Cron：
MVP 阶段追求简单，APScheduler 在进程内跑，零外部依赖。
后续如果需要更可靠的调度，再切到平台级 cron + webhook。

时区说明：
中国用户凌晨 5:00（UTC+8）= UTC 前一天 21:00。
APScheduler 的 cron trigger 默认用 UTC，所以 hour=21, day_before=true。
"""
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.repositories import content_repo
from app.schemas import THEME_OPTIONS
from app.services.news_generator import generate_daily_news_batch

log = logging.getLogger(__name__)

# 要定时生成的主题列表（排除 all_random 和 custom，这两个不适合预生成）
_THEMES = [t for t in THEME_OPTIONS if t not in ("all_random", "custom")]

scheduler = BackgroundScheduler()


def _daily_generate_job():
    """
    每日定时任务：为每个 theme 生成 3 篇新闻。

    幂等设计：同 theme 今日已有内容时跳过，避免重复调用 LLM。
    每个 theme 独立 DB session，单个失败不影响其他 theme。
    """
    log.info("定时任务启动：开始生成今日 AI 新闻 themes=%s", _THEMES)
    today = date.today()
    success_count = 0
    skip_count = 0
    fail_count = 0

    for theme in _THEMES:
        db = SessionLocal()
        try:
            # 幂等检查：今天已生成则跳过
            existing = content_repo.get_today_ai_contents_by_theme(db, theme)
            if len(existing) >= 4:
                log.debug("theme=%s 今日已生成 %s 条，跳过", theme, len(existing))
                skip_count += 1
                continue

            # 调用 LLM 生成 3 篇新闻（async 函数，在同步上下文中用 _run_async 桥接）
            batch = _run_async(generate_daily_news_batch(theme=theme))

            if not batch or not batch[0].get("article"):
                log.warning("theme=%s AI 返回内容为空，跳过", theme)
                fail_count += 1
                continue

            # 写入数据库
            content_ids = []
            for data in batch:
                content = content_repo.create_ai_content(db, data)
                content_ids.append(content.content_id)

            db.commit()
            success_count += 1
            log.info("theme=%s 生成完成 content_ids=%s", theme, content_ids)

        except Exception as e:
            db.rollback()
            log.error("theme=%s 生成失败: %s", theme, e)
            fail_count += 1
        finally:
            db.close()

    log.info(
        "定时任务完成：成功=%s 跳过=%s 失败=%s",
        success_count, skip_count, fail_count,
    )


def _run_async(coro):
    """在同步上下文中运行异步协程。"""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def start_scheduler():
    """启动定时任务调度器，注册每日生成 job。"""
    # 每天凌晨 5:00 CST = UTC 21:00（前一天）
    # hour=21, minute=0, 第二天执行
    scheduler.add_job(
        _daily_generate_job,
        trigger=CronTrigger(hour=21, minute=0),
        id="daily_news_generate",
        name="每日 AI 新闻生成",
        replace_existing=True,
    )
    scheduler.start()
    log.info("定时任务调度器已启动，每日 05:00 CST 执行新闻生成")


def shutdown_scheduler():
    """关闭定时任务调度器。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        log.info("定时任务调度器已关闭")
