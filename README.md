# compact-counter-concept

> **Compaction Count — the overlooked inverse health metric for LLM context windows.**
> **压缩次数 —— 一个被忽略的 LLM 上下文健康度反向指标。**

<p align="center">
  <img src="assets/terminal-three-states.png" alt="Three states: Healthy (0 compactions), Warning (2), Critical (4)" width="100%">
</p>

---

## Production Implementation / 生产实现

**[`compact-counter.py`](compact-counter.py)** — Claude Code hook-based, validated across multiple compaction cycles. Drop it into `~/.claude/scripts/` and configure 3 hooks. Done.

```bash
# Installation (one-time)
cp compact-counter.py ~/.claude/scripts/
# Then add PreCompact, PostCompact, SessionStart hooks to ~/.claude/settings.json
# See deepseek-claude-code-starter for full config
```

| Hook | What it does |
|------|-------------|
| **PreCompact** | Increments counter, injects count into compaction summary so it survives |
| **PostCompact** | Updates completion timestamp, syncs statusline for real-time display |
| **SessionStart** | `startup` → new session, `compact` → resume with reminder, `clear` → reset |

**Key implementation details:**
- Uses `hook_event_name` from JSON payload for reliable event detection
- Regex fallback for PostCompact's 14K+ character `compact_summary` payloads
- Atomic JSON state persistence (`~/.claude/compact-state.json`)
- Statusline sync for real-time status bar display
- Windows GBK emoji compatibility

Already integrated into **[deepseek-claude-code-starter](https://github.com/YuhaoLin2005/deepseek-claude-code-starter)** — one command to install everything.

---

## Try It Yourself / 你自己试一下

```bash
# How many times has YOUR session been compacted?
grep -ri "compact\|compression\|压缩" ~/.deepseek-tui/ ~/.claude/ 2>/dev/null | wc -l
```

If the number is > 0: your tool already has compaction events in its logs. It's counting them. It's just not showing you.
如果结果 > 0：你的工具已经在日志里记录压缩事件了。它在计数，只是没告诉你。

---

## What This Is / 这是什么

While building a [Claude Code + DeepSeek config pack](https://github.com/YuhaoLin2005/deepseek-claude-code-starter), I noticed: the status bar shows context usage (room left), but **how much information has already been lost** — nothing tells you that.

Existing tools do progress bars (HUD), predictions (cccontext), lookbacks (ctx-inspector), composite scores (noctrace). **None of them surface "compaction count" as a standalone, real-time metric.**

This repo is an open initiative proposing that they should.

在做 [Claude Code + DeepSeek 配置包](https://github.com/YuhaoLin2005/deepseek-claude-code-starter) 的过程中，我发现状态栏显示上下文占比（还剩多少空间），但**已经丢了多少信息**——没有任何工具告诉你。市面上的工具做进度条、做预测、做回溯、做综合评分——**没有一个人把"压缩次数"单独拿出来。** 这个仓库是一份开放倡议：他们应该加。

---

## The Concept / 概念设计

```
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│  🟢 Healthy / 健康      │ │  🟡 Warning / 警告       │ │  🔴 Critical / 严重      │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │
│  🔄 Compacted: 0        │ │  🔄 Compacted: 2        │ │  🔄 Compacted: 4        │
│  📊 Context: 23%        │ │  📊 Context: 68%        │ │  📊 Context: 91%        │
│  💰 $0.05               │ │  💰 $0.18               │ │  💰 $0.31               │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  ✅ Full memory         │ │  ⚠️ Partial info lost   │ │  💀 High hallucination   │
│  Model fully grasps     │ │  Watch reply quality.   │ │  Reset immediately!      │
│  all context.           │ │  Avoid complex tasks.   │ │  /reset or /rewind       │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

**0 compactions → 🟢 proceed. &nbsp;&nbsp; 2 compactions → 🟡 watch. &nbsp;&nbsp; 4 compactions → 🔴 reset.**

为什么是压缩次数而不是上下文百分比？因为次数单向累积、客观可测、直接反映信息丢失。[完整论证 →](docs/idea.md)

---

## Competitive Positioning / 竞争定位

Compaction count doesn't compete with existing tools. It fills the **"cumulative damage log"** they all leave empty.
压缩次数不跟现有工具竞争。它补上的是它们都漏掉的**"累计损伤记录"**：

| Tool | Answers | Analogy |
|------|---------|---------|
| Claude HUD (progress bar) | "Room left?" | Fuel gauge / 油量表 |
| cccontext (prediction) | "Compaction coming?" | Nav alert / 导航提醒 |
| ctx-inspector (lookback) | "What happened?" | Dashcam / 行车记录仪 |
| noctrace (scoring) | "Overall health?" | Vehicle score / 车况评分 |
| **Compaction Count** | **"Compacted N times?"** | **Accident log / 事故记录表** |

They are not competitors. They are different gauges on the same dashboard.
它们不是竞品，是同一块仪表盘的不同仪表。[完整对比 →](docs/competitive-analysis.md)

---

## FAQ

<details>
<summary><b>Isn't this just three lines of code? / 这不就三行代码？</b></summary>

Yes. The implementation is trivial. What's not trivial is the product judgment of *which number to surface*. Nobody picked compaction count before. This repo argues for that choice.

实现确实简单。不简单的是"在状态栏显示哪个数字"这个产品判断。从来没人选压缩次数。这个仓库在论证这个选择。

</details>

<details>
<summary><b>Won't official tools just build this? / 官方自己做了呢？</b></summary>

That's the best outcome. The repo's value is in first identifying *why* this metric matters. If Anthropic or DeepSeek ships it, the insight was correct. That's a win.

最好的结果。仓库的价值在于首先识别并论证了这个指标为什么重要。官方做了 = 洞察正确 = 赢了。

</details>

<details>
<summary><b>Where do the thresholds come from? / 阈值从哪来的？</b></summary>

Informed starting points based on usage patterns, not data-proven. The next step is correlating compaction count with user `/reset` behavior. The framework for that data exists here. The numbers will shift.

基于使用观察的合理起点，不是数据验证过的。下一步是分析压缩次数和用户 `/reset` 行为的相关性。

</details>

<details>
<summary><b>Why count instead of "retention %"? / 为什么是次数不是保持率？</b></summary>

Retention is an estimate. Count is a fact. Users build intuition around "4 compactions = bad" faster than around "31.7% retention."

保持率是估算，次数是事实。用户对"4次=危险"的直觉建立比"31.7%"快得多。

</details>

<details>
<summary><b>Is this too niche? / 太小众了吧？</b></summary>

Every heavy LLM CLI user experiences the downstream effects — they just don't attribute it to compaction. "AI gets dumber in long sessions" is universal. This metric connects that complaint to a specific, measurable cause.

每个重度 LLM CLI 用户都体验过——只是不知道是压缩导致的。"长会话中 AI 越来越笨"是普遍抱怨，这个指标把它连接到了具体原因。

</details>

---

## Let's Make This Happen / 一起推动

For tool teams: **this is a trivially cheap optimization.** Compaction events are already logged — count and display. The UX change is fundamental: black box → a crack of white.

对工具团队：**实现成本趋近于零。** 压缩事件已在日志里，计数就行。UX 改变是根本性的：黑盒 → 有一点白。

- **File a Feature Request** with your LLM tool — paste the mockup above
- **PR to this repo** — monitor scripts for more tools (Aider, Cursor, ChatGPT plugin, etc.)
- **Share** — V2EX, Reddit, Discord, Hacker News. Ask: "would compaction count change when you reset?"
- **Challenge it** — think compaction count is the wrong signal? Open an Issue. Convincing us otherwise is also a contribution.

See [CONTRIBUTING.md](CONTRIBUTING.md) for implementation details.

---

## Docs / 更多文档

| Doc | Content |
|-----|---------|
| [docs/idea.md](docs/idea.md) | Core concept: why count > percentage / 核心理念 |
| [docs/competitive-analysis.md](docs/competitive-analysis.md) | Tool-by-tool comparison + originality argument / 竞品对比 |
| [docs/validation.md](docs/validation.md) | Full validation path: Phase 1 → 2 → 3 / 验证路径 |
| [docs/architecture.md](docs/architecture.md) | Design decisions: why 3 metrics, not 5 / 架构思路 |

## License

MIT © 2026 YuhaoLin2005

> This proposal is public. If an LLM tool team ships something similar — that's what proving the value of an insight looks like.
