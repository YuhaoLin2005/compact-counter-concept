# compact-counter

Claude Code 上下文压缩次数监控。不是简单的"越少越好"——压缩有最佳区间。

## 核心发现

基于 70+ 次会话的实际体验：

| 压缩次数 | 状态 | AI表现 |
|---------|------|--------|
| 0 | 记忆完整 | 上下文完整，但噪声多，响应偏慢 |
| 1-2 | 最佳区间 | 上下文被提炼，去除冗余，**变聪明** |
| 3-4 | 临界 | 开始丢失边缘信息，复杂任务需验证 |
| 5+ | 过压 | 上下文严重失真，**明显变笨**，建议新开会话 |

**结论**：压缩不是线性退化——前几次压缩提升表现（去除噪声聚焦关键信息），超过阈值后劣化（核心上下文被截断）。5 次是红线。

## 效果

![状态栏截图](assets/terminal-three-states.png)

状态栏显示 `压缩:2` 或 `记忆完整`。

## 快速使用

```bash
cp compact-counter.py ~/.claude/scripts/

# settings.json 配置 PreCompact/PostCompact/SessionStart 三个 hook
# 完整配置见 deepseek-claude-code-starter
```

## 原理

统计 Claude Code hook 事件中的 compact 次数，持久化到 `~/.claude/compact-state.json`，状态栏实时显示。三个 hook 分别在会话启动/压缩前/压缩后更新计数。

## 已知局限

- 多会话会累加（不自动重置）
- 仅测试过 Windows
- 不会自动刷新，需手动运行

## License

MIT
