# compact-counter

Claude Code 上下文压缩次数监控。不是线性退化——压缩对AI表现的影响是非线性的，且**不同模型之间存在差异**。

## 核心发现

基于 DeepSeek V4 (1M context) 70+ 次会话的实际体验：

| 压缩次数 | 状态 | 表现（DeepSeek V4 实测） |
|---------|------|------------------------|
| 0 | 记忆完整 | 上下文完整，但噪声多，响应偏慢 |
| 1-2 | 最佳区间 | 上下文被提炼，去除冗余，**变聪明** |
| 3-4 | 临界 | 开始丢失边缘信息，复杂任务需验证 |
| 5+ | 过压 | 上下文严重失真，**明显变笨**，新开会话 |

**关键前提**：
- 上述阈值基于 DeepSeek V4 1M 上下文窗口的实测
- 不同模型（Claude/ GPT/ Gemini）因上下文窗口大小、压缩算法、记忆机制不同，阈值**会有差异**
- 本工具的价值不是提供"通用标准"，而是**帮你找到你自己所用模型的最佳区间**

## 效果

![状态栏截图](assets/terminal-three-states.png)

## 快速使用

```bash
cp compact-counter.py ~/.claude/scripts/
# settings.json 配置 PreCompact/PostCompact/SessionStart 三个 hook
```

## 原理

统计 Claude Code hook 事件中的 compact 次数，持久化到 `~/.claude/compact-state.json`，状态栏实时显示。

## 已知局限

- 阈值基于单一模型（DeepSeek V4），不同模型需实测校准
- 多会话累加（不自动重置）
- 仅测试过 Windows
- 不自动刷新，需手动运行

## License

MIT
