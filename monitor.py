#!/usr/bin/env python3
"""
Compact Counter — 概念验证框架

这是一个产品设计提案的配套原型，目的不是上线运行，而是：
1. 证明"监控日志 → 检测压缩 → 分级告警"在技术上是可行的
2. 用可运行的代码来沟通设计意图（比 PRD 文字更具体）
3. 给未来的实际实现一个明确的起点

如果你看到这段代码并想"这不够健壮"——你说得对。
这是概念验证阶段故意保留的"不完整"，让后续讨论有具体的锚点。

>>> 生产实现已就绪: compact-counter.py <<<
生产版直接使用 Claude Code hooks（PreCompact/PostCompact/SessionStart），
不依赖日志文件正则解析。见同仓库 compact-counter.py。

Usage (for demo purposes):
    python monitor.py                          # 默认配置
    python monitor.py --log-path session.log   # 指定日志
    python monitor.py --warning 2 --critical 4 # 自定义阈值
    python monitor.py --notify                 # 启用桌面通知
"""

from __future__ import annotations

import argparse
import logging
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


class State(Enum):
    HEALTHY = auto()    # 0-1 次压缩
    WARNING = auto()    # 2-3 次压缩
    CRITICAL = auto()   # 4+ 次压缩

    @property
    def icon(self) -> str:
        return {State.HEALTHY: "🟢", State.WARNING: "🟡", State.CRITICAL: "🔴"}[self]

    @property
    def label(self) -> str:
        return {
            State.HEALTHY: "健康",
            State.WARNING: "轻度警告",
            State.CRITICAL: "严重警告",
        }[self]

    @property
    def advice(self) -> str:
        return {
            State.HEALTHY: "✅ 完整记忆 — 模型完全掌握所有上下文。",
            State.WARNING: "⚠️ 部分信息已丢失 — 建议留意回答质量，不推荐新增复杂任务。",
            State.CRITICAL: "💀 高度幻觉风险 — 强烈建议立即重置！执行 /reset 或 /rewind 到早期节点。",
        }[self]


@dataclass
class SessionStatus:
    """当前会话的压缩状态快照."""

    compression_count: int = 0
    state: State = State.HEALTHY
    session_start: datetime = field(default_factory=datetime.now)
    last_compression_at: Optional[datetime] = None
    last_alert_at: Optional[datetime] = None

    @property
    def context_retention_estimate(self) -> int:
        """估算上下文保持率（百分比）. 经验公式."""
        return max(10, 100 - self.compression_count * 22)


# ---------------------------------------------------------------------------
# 压缩检测引擎
# ---------------------------------------------------------------------------

# 默认检测正则 — 覆盖中英文压缩关键词
DEFAULT_PATTERNS: list[str] = [
    r"compact(?:ing|ed)?\s+(?:context|history|conversation)",
    r"compression\s+(?:event|triggered|complete|finished)",
    r"compacting\s+(?:context|history)",
    r"auto[-_]?compact",
    r"(?:context|history)\s+(?:compaction|summarization)",
    r"summarizing\s+(?:conversation|context|history)",
    r"pruning\s+(?:context|messages|history)",
    r"context\s+window\s+exceeded",
    # 中文
    r"正在压缩(?:对话|上下文|历史)",
    r"(?:上下文|对话|历史)压缩",
    r"压缩对话(?:记录|历史)?",
    r"自动压缩",
]


def compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    """编译正则表达式列表, 跳过无效模式."""
    compiled: list[re.Pattern[str]] = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, re.IGNORECASE))
        except re.error as exc:
            logging.warning("无效正则跳过: %r — %s", p, exc)
    return compiled


class CompressionDetector:
    """日志行压缩事件检测器."""

    def __init__(self, patterns: list[str] | None = None) -> None:
        self._patterns = compile_patterns(patterns or DEFAULT_PATTERNS)

    def is_compression_event(self, line: str) -> bool:
        """判断一行日志是否包含压缩事件."""
        if not line.strip():
            return False
        return any(p.search(line) for p in self._patterns)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)


# ---------------------------------------------------------------------------
# 告警处理器
# ---------------------------------------------------------------------------

AlertHandler = Callable[[State, SessionStatus], None]


def terminal_alert(state: State, status: SessionStatus) -> None:
    """终端颜色输出告警."""
    colors = {State.HEALTHY: "\033[92m", State.WARNING: "\033[93m", State.CRITICAL: "\033[91m"}
    reset = "\033[0m"
    color = colors.get(state, "")

    print(f"\n{color}┌{'─' * 50}┐{reset}")
    print(f"{color}│ {state.icon} 压缩告警: {state.label}{reset}")
    print(f"{color}├{'─' * 50}┤{reset}")
    print(f"{color}│   压缩次数: {status.compression_count} 次{reset}")
    print(f"{color}│   上下文保持率: ~{status.context_retention_estimate}%{reset}")
    print(f"{color}│   上次压缩: {status.last_compression_at or 'N/A'}{reset}")
    print(f"{color}│{reset}")
    print(f"{color}│   {state.advice}{reset}")
    print(f"{color}└{'─' * 50}┘{reset}\n")


def desktop_notify(state: State, status: SessionStatus) -> None:
    """桌面通知 (需要 pip install plyer)."""
    try:
        from plyer import notification  # type: ignore[import-untyped]
        notification.notify(
            title=f"Compact Counter — {state.label}",
            message=(
                f"压缩 {status.compression_count} 次 | "
                f"上下文保持 ~{status.context_retention_estimate}%"
            ),
            timeout=10,
        )
    except ImportError:
        logging.warning("plyer 未安装, 无法发送桌面通知")


# ---------------------------------------------------------------------------
# 监控主逻辑
# ---------------------------------------------------------------------------


class CompactMonitor:
    """压缩事件主监控器."""

    def __init__(
        self,
        log_path: str | Path,
        *,
        warning_threshold: int = 2,
        critical_threshold: int = 4,
        poll_interval: float = 2.0,
        alert_cooldown: float = 300.0,
        alert_handlers: list[AlertHandler] | None = None,
        patterns: list[str] | None = None,
    ) -> None:
        self.log_path = Path(log_path).expanduser().resolve()
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.poll_interval = poll_interval
        self.alert_cooldown = alert_cooldown
        self.alert_handlers = alert_handlers or [terminal_alert]
        self.detector = CompressionDetector(patterns)

        self.status = SessionStatus()
        self._running = False
        self._last_size = 0

    # ---- 文件跟踪 --------------------------------------------------------

    def _ensure_log_exists(self) -> bool:
        """确保日志文件存在, 不存在时等待."""
        if self.log_path.exists():
            return True
        logging.info("等待日志文件创建: %s", self.log_path)
        return False

    def _read_new_lines(self) -> list[str]:
        """读取日志文件的新增行."""
        try:
            current_size = self.log_path.stat().st_size
        except FileNotFoundError:
            return []

        if current_size < self._last_size:
            # 日志被截断/轮转 — 从头开始
            self._last_size = 0
            logging.info("检测到日志轮转, 重新读取")

        if current_size == self._last_size:
            return []

        with open(self.log_path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(self._last_size)
            new_content = fh.read()

        self._last_size = current_size
        return new_content.splitlines()

    # ---- 状态判定 --------------------------------------------------------

    def _determine_state(self) -> State:
        count = self.status.compression_count
        if count >= self.critical_threshold:
            return State.CRITICAL
        if count >= self.warning_threshold:
            return State.WARNING
        return State.HEALTHY

    # ---- 告警冷却 --------------------------------------------------------

    def _should_alert(self) -> bool:
        """是否应该发送告警 (冷却期外)."""
        if self.status.last_alert_at is None:
            return True
        elapsed = (datetime.now() - self.status.last_alert_at).total_seconds()
        return elapsed >= self.alert_cooldown

    # ---- 事件处理 --------------------------------------------------------

    def _handle_compression(self) -> None:
        """处理检测到的压缩事件."""
        self.status.compression_count += 1
        self.status.last_compression_at = datetime.now()
        new_state = self._determine_state()

        logging.info(
            "检测到压缩 #%d | 状态: %s | 估算保持率: ~%d%%",
            self.status.compression_count,
            new_state.label,
            self.status.context_retention_estimate,
        )

        # 状态升级或达到阈值时发告警
        if new_state != self.status.state or self._should_alert():
            if self._should_alert():
                for handler in self.alert_handlers:
                    try:
                        handler(new_state, self.status)
                    except Exception:
                        logging.exception("告警处理器异常")
                self.status.last_alert_at = datetime.now()

        self.status.state = new_state

    # ---- 运行循环 --------------------------------------------------------

    def start(self) -> None:
        """启动监控循环."""
        self._running = True
        logging.info(
            "Compact Counter 已启动 | 日志: %s | 阈值: W=%d C=%d | 轮询: %.1fs",
            self.log_path,
            self.warning_threshold,
            self.critical_threshold,
            self.poll_interval,
        )
        print(f"🔍 监控中: {self.log_path}")
        print(f"   告警阈值: 🟡 {self.warning_threshold} 次 → 🔴 {self.critical_threshold} 次")
        print(f"   按 Ctrl+C 停止\n")

        while self._running:
            if not self._ensure_log_exists():
                time.sleep(self.poll_interval)
                continue

            new_lines = self._read_new_lines()
            for line in new_lines:
                if self.detector.is_compression_event(line):
                    logging.debug("匹配压缩行: %.200s", line)
                    self._handle_compression()

            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """停止监控."""
        self._running = False
        logging.info("Compact Counter 已停止 | 共检测到 %d 次压缩", self.status.compression_count)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compact Counter — 压缩次数监控（概念验证）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--log-path",
        default="~/.deepseek-tui/logs/session.log",
        help="日志文件路径 (default: ~/.deepseek-tui/logs/session.log)",
    )
    parser.add_argument(
        "--warning",
        type=int,
        default=2,
        help="警告阈值 — 压缩次数 (default: 2)",
    )
    parser.add_argument(
        "--critical",
        type=int,
        default=4,
        help="严重阈值 — 压缩次数 (default: 4)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="日志轮询间隔 — 秒 (default: 2.0)",
    )
    parser.add_argument(
        "--alert-cooldown",
        type=float,
        default=300.0,
        help="告警冷却时间 — 秒 (default: 300)",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="启用桌面通知",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="后台守护模式运行",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="详细日志输出",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    # 日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 告警处理器
    handlers: list[AlertHandler] = [terminal_alert]
    if args.notify:
        handlers.append(desktop_notify)

    monitor = CompactMonitor(
        log_path=args.log_path,
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        poll_interval=args.poll_interval,
        alert_cooldown=args.alert_cooldown,
        alert_handlers=handlers,
    )

    # 信号处理 — 优雅退出
    def _shutdown(signum: int, frame: object) -> None:
        print("\n⏹ 收到中断信号, 正在退出...")
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # 后台模式
    if args.daemon:
        import os
        pid = os.fork()
        if pid > 0:
            print(f"守护进程已启动 (PID: {pid})")
            sys.exit(0)
        # 子进程继续
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.stop()
    except Exception:
        logging.exception("监控异常退出")
        sys.exit(1)


if __name__ == "__main__":
    main()
