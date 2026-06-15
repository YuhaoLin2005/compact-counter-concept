"""概念验证：压缩检测 & 状态转换逻辑的测试.

这个测试文件的目的不是追求覆盖率，而是证明：
1. 正则匹配是可靠的
2. 状态转换逻辑是明确的
3. 阈值边界是清晰的
"""

import pytest
from datetime import datetime, timedelta

from monitor import (
    CompressionDetector,
    SessionStatus,
    State,
    CompactMonitor,
)


# ---------------------------------------------------------------------------
# 模式匹配测试
# ---------------------------------------------------------------------------

class TestCompressionDetector:
    """验证中英文压缩关键词都能被正确检测."""

    @pytest.fixture
    def detector(self) -> CompressDetector:
        return CompressDetector()

    @pytest.mark.parametrize("line", [
        "[INFO] compacting context...",
        "[SYSTEM] Compact context triggered",
        "context compaction complete",
        "auto-compact finished",
        "compacting history",
        "compression event: context",
    ])
    def test_english_patterns(self, detector: CompressDetector, line: str) -> None:
        assert detector.is_compression_event(line), f"应命中: {line!r}"

    @pytest.mark.parametrize("line", [
        "[SYSTEM] 正在压缩对话...",
        "[INFO] 上下文压缩完成",
        "对话压缩: 已总结前 50 条消息",
        "自动压缩触发",
        "压缩对话记录",
        "历史压缩完成",
    ])
    def test_chinese_patterns(self, detector: CompressDetector, line: str) -> None:
        assert detector.is_compression_event(line), f"应命中: {line!r}"

    @pytest.mark.parametrize("line", [
        "[USER] compress this file",
        "compacting the soil for the garden",  # 不是 AI 上下文压缩
        "the compression algorithm",
        "[INFO] token count: 12345",          # 普通日志
        "",                                    # 空行
        "   ",                                # 空白行
    ])
    def test_false_positives(self, detector: CompressDetector, line: str) -> None:
        """确保不会对普通日志误报."""
        assert not detector.is_compression_event(line), f"不应命中: {line!r}"


# ---------------------------------------------------------------------------
# 状态转换测试
# ---------------------------------------------------------------------------

class TestStateTransitions:
    """验证阈值边界和状态升级逻辑."""

    @pytest.fixture
    def monitor(self, tmp_path):
        """创建一个指向临时文件的 monitor."""
        log_file = tmp_path / "session.log"
        log_file.touch()
        return CompactMonitor(
            log_path=log_file,
            warning_threshold=2,
            critical_threshold=4,
            poll_interval=0.01,
            alert_cooldown=9999,  # 测试中不需要冷却
        )

    def test_initial_state(self, monitor):
        """初始状态应为 HEALTHY."""
        assert monitor.status.compression_count == 0
        assert monitor.status.state == State.HEALTHY

    def test_healthy_to_warning(self, monitor):
        """第 2 次压缩应触发 WARNING."""
        # 模拟 2 次压缩
        for _ in range(2):
            monitor._handle_compression()
        assert monitor.status.compression_count == 2
        assert monitor.status.state == State.WARNING

    def test_warning_to_critical(self, monitor):
        """第 4 次压缩应触发 CRITICAL."""
        for _ in range(4):
            monitor._handle_compression()
        assert monitor.status.compression_count == 4
        assert monitor.status.state == State.CRITICAL

    def test_state_never_goes_back(self, monitor):
        """状态只升不降 — 压缩次数不会自动减少."""
        for _ in range(5):
            monitor._handle_compression()
        assert monitor.status.state == State.CRITICAL
        # 状态应该保持 CRITICAL
        assert monitor._determine_state() == State.CRITICAL


# ---------------------------------------------------------------------------
# 上下文保持率估算
# ---------------------------------------------------------------------------

class TestContextRetention:
    """验证保持率估算逻辑."""

    def test_zero_compressions(self):
        status = SessionStatus(compression_count=0)
        assert status.context_retention_estimate == 100

    def test_two_compressions(self):
        status = SessionStatus(compression_count=2)
        assert status.context_retention_estimate == 56  # 100 - 2*22

    def test_four_compressions(self):
        status = SessionStatus(compression_count=4)
        assert status.context_retention_estimate == 12  # max(10, 100-4*22)

    def test_floor_at_ten_percent(self):
        """保持率不低于 10% — 极端情况也有底线."""
        status = SessionStatus(compression_count=10)
        assert status.context_retention_estimate == 10


# ---------------------------------------------------------------------------
# State 枚举展示值
# ---------------------------------------------------------------------------

class TestStateDisplay:
    """验证三个状态的图标和文字正确."""

    def test_icons(self):
        assert State.HEALTHY.icon == "🟢"
        assert State.WARNING.icon == "🟡"
        assert State.CRITICAL.icon == "🔴"

    def test_labels(self):
        assert "健康" in State.HEALTHY.label
        assert "警告" in State.WARNING.label
        assert "严重" in State.CRITICAL.label

    def test_advice_is_actionable(self):
        """三个状态都应该给出明确的行动建议."""
        for state in State:
            assert len(state.advice) > 0
            # 严重状态必须提到"重置"
            if state == State.CRITICAL:
                assert "重置" in state.advice or "reset" in state.advice.lower()
