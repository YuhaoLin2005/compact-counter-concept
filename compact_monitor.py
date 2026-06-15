#!/usr/bin/env python3
"""
DeepSeek-TUI 压缩次数监控器 (ARCHIVED)
用法: python3 compact_monitor.py

⚠️ 此文件为早期概念原型，已归档。生产实现见 compact-counter.py。
   compact-counter.py 直接使用 Claude Code hooks（PreCompact/PostCompact/SessionStart），
   不依赖日志文件正则解析。建议使用生产版本。
"""

import time
import os
import re

LOG_PATH = os.path.expanduser("~/.local/share/deepseek-tui/session.log")
# 如果日志路径不对，请修改


def get_compact_count():
    if not os.path.exists(LOG_PATH):
        return 0
    with open(LOG_PATH, 'r') as f:
        content = f.read()
    # 匹配压缩事件的关键词，根据实际输出调整
    matches = re.findall(r'compaction|compact|压缩', content, re.I)
    return len(matches)


def main():
    print("监控 DeepSeek-TUI 压缩次数，按 Ctrl+C 退出")
    while True:
        count = get_compact_count()
        print(f"\r🔄 当前会话压缩次数: {count}  ", end='', flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
