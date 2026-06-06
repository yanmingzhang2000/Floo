"""日志初始化。

为什么集中放在这里：CLAUDE.md 规则三要求所有分支处都用 log.debug 记录，
各模块只需要 `log = logging.getLogger(__name__)` 即可，不再各自配置 handler，
避免日志格式漂移。
"""
import logging
import sys


def setup_logging(level: str = "DEBUG") -> None:
    """在应用启动时调用一次。

    为什么默认 DEBUG：MVP 阶段排查问题优先于性能；后续上线再按需改成
    通过请求头按需开启（参考 CLAUDE.md 提到的 override_enabled 机制）。
    """
    root = logging.getLogger()
    if root.handlers:
        # 已经初始化过（uvicorn --reload 会重复触发），不再重复挂 handler
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)
