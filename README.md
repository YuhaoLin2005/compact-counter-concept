# compact-counter

> 在 Claude Code 状态栏显示上下文压缩次数。压缩越多，信息丢失越严重，看到 3+ 次就该 `/reset` 了。

<p align="center">
  <img src="assets/terminal-three-states.png" alt="Three states: Healthy (0 compactions), Warning (2), Critical (4)" width="100%">
</p>

---

## 这是什么

在折腾 [Claude Code + DeepSeek 配置](https://github.com/YuhaoLin2005/deepseek-claude-code-starter) 的过程中，发现 Claude Code 日志里会记录 compaction 事件，顺手做了一个在状态栏显示次数的脚本。

只是一个几十行的小脚本，不解决根本问题，但能让你心里有数——知道什么时候该 `/reset`。

---

## 实现

**[`compact-counter.py`](compact-counter.py)** — 基于 Claude Code hook，读取日志中的 compact 事件，显示次数（0 / 1-2 / 3+）。

```bash
# 安装（一次性）
cp compact-counter.py ~/.claude/scripts/
# 然后在 ~/.claude/settings.json 里配 PreCompact、PostCompact、SessionStart 三个 hook
# 完整配置见 deepseek-claude-code-starter
```

| Hook | 作用 |
|------|------|
| **PreCompact** | 计数器 +1，把当前次数写入压缩摘要，让它跨 compact 存活 |
| **PostCompact** | 更新时间戳，同步状态行 |
| **SessionStart** | `startup` → 新会话，`compact` → 恢复提醒，`clear` → 重置 |

**实现要点：**
- 从 JSON payload 里读 `hook_event_name` 判断事件类型
- PostCompact 的 `compact_summary` 有 14K+ 字符，用正则兜底匹配
- JSON 状态持久化到 `~/.claude/compact-state.json`
- 状态行实时同步
- Windows GBK emoji 兼容

已集成到 **[deepseek-claude-code-starter](https://github.com/YuhaoLin2005/deepseek-claude-code-starter)**。

---

## 自己试一下

```bash
# 看看你的会话已经被压缩了几次
grep -ri "compact\|compression\|压缩" ~/.deepseek-tui/ ~/.claude/ 2>/dev/null | wc -l
```

如果结果 > 0：你的工具已经在日志里记录压缩事件了。它在计数，只是没告诉你。

---

## 概念

```
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│  🟢 健康                 │ │  🟡 注意                 │ │  🔴 危险                 │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │
│  🔄 Compacted: 0        │ │  🔄 Compacted: 2        │ │  🔄 Compacted: 4        │
│  📊 Context: 23%        │ │  📊 Context: 68%        │ │  📊 Context: 91%        │
│  💰 $0.05               │ │  💰 $0.18               │ │  💰 $0.31               │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  ✅ 完整记忆             │ │  ⚠️ 部分信息已丢失       │ │  💀 高幻觉风险            │
│  模型拥有完整上下文。     │ │  留意回复质量。          │ │  建议立即 /reset。        │
│                          │ │  避免复杂任务。          │ │                          │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

**0 次 → 🟢 正常。&nbsp;&nbsp; 2 次 → 🟡 注意。&nbsp;&nbsp; 4 次 → 🔴 该 reset 了。**

为什么是压缩次数而不是上下文百分比？因为次数单向累积、客观可测、直接反映信息丢失。[详细说明 →](docs/idea.md)

---

## 和其他工具的对比

压缩次数不跟现有工具竞争，它补的是另一个维度：

| 工具 | 回答了什么问题 | 类比 |
|------|--------------|------|
| Claude HUD（进度条） | "还剩多少空间？" | 油量表 |
| cccontext（预测） | "快压缩了？" | 导航提醒 |
| ctx-inspector（回溯） | "发生了什么？" | 行车记录仪 |
| noctrace（评分） | "整体健康度？" | 车况评分 |
| **压缩次数** | **"压缩了几次？"** | **事故记录表** |

只是同一块仪表盘上的不同仪表。[完整对比 →](docs/competitive-analysis.md)

---

## FAQ

<details>
<summary><b>这不就几行代码？</b></summary>

对，实现很简单。不简单的是判断"状态栏该显示哪个数字"——以前没人选压缩次数。这个仓库在论证这个选择。

</details>

<details>
<summary><b>官方自己做了呢？</b></summary>

那是最好的结果。仓库的价值在于先识别并论证了这个指标为什么有用。官方做了 = 洞察正确 = 没白折腾。

</details>

<details>
<summary><b>阈值哪来的？</b></summary>

基于使用观察的合理起点，不是数据验证过的。下一步可以分析压缩次数和用户 `/reset` 行为的相关性。数字会调整。

</details>

<details>
<summary><b>为什么是次数不是"保留率"？</b></summary>

保留率是估算，次数是事实。用户对"4次=危险"的直觉建立比"31.7%"快得多。

</details>

<details>
<summary><b>太小众了吧？</b></summary>

每个重度 LLM CLI 用户都体验过"长会话中 AI 越来越笨"——只是不知道是压缩导致的。这个指标把它连接到了具体原因。

</details>

---

## 文档

| 文件 | 内容 |
|-----|------|
| [docs/idea.md](docs/idea.md) | 核心理念：为什么次数 > 百分比 |
| [docs/competitive-analysis.md](docs/competitive-analysis.md) | 逐工具对比 |
| [docs/validation.md](docs/validation.md) | 验证路径 |
| [docs/architecture.md](docs/architecture.md) | 架构思路 |

## License

MIT © 2026 YuhaoLin2005
