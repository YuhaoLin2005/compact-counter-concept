# compact-counter-concept / 压缩次数

> **Compaction Count — the overlooked inverse health metric for LLM context windows.**
>
> **压缩次数 —— 一个被忽略的上下文健康度反向指标。**
>
> From black box to white box. One number in the status bar is all it takes.
> 从黑盒到白盒，只需要在状态栏多显示一个数字。

---

## What This Is / 这是什么

While building a Claude Code + DeepSeek configuration pack, I noticed a detail:
在做 Claude Code + DeepSeek 配置包的过程中，我发现了一个细节：

The status bar shows context usage (how much room is left), and triggers compaction at a threshold. But **how much information has already been lost** — nothing tells you that.
状态栏显示上下文占比（还剩多少空间），到阈值就触发压缩。但**已经丢了多少信息**——没有任何工具告诉你。

I looked around. Existing context visualization tools do progress bars, predictions, historical lookups, composite health scores — **none of them surface "compaction count" as a standalone, real-time health metric.**
翻了一圈市面上已有的上下文可视化工具，它们做进度条、做预测、做回溯、做综合评分——**没有一个人把"压缩次数"单独拿出来，作为一个实时可见的健康指标。**

This repo turns that observation into a full proposal: why this metric matters, how it relates to existing tools (complementary, not competitive), and a runnable proof-of-concept framework.
这个仓库把这一观察写成了一份完整提案：为什么这个指标重要、它和现有工具的关系（互补不是替代）、以及一个可运行的概念验证框架。

**It's an open initiative, aimed at the developers and users of LLM CLI tools.**
**它是一份开放倡议，面向 LLM CLI 工具的开发者和用户社区。**

---

## 一、How This Idea Came About / 这个想法是怎么来的

### A Concrete Afternoon / 一个具体的下午

I was building myself a Claude Code + DeepSeek config pack — the existing setups were uncomfortable. Price mapping was off, visual capability was missing, security guards were absent.
我在给自己做一套 Claude Code 接 DeepSeek 的配置包——因为现有的配置用着不舒服，价格映射不准，视觉能力缺失，安全护栏也没有。

Eight hours, fully conversing with AI. I did requirements, testing, decisions; AI handled execution.
全程和 AI 对话 8 小时。我负责提需求、测试、决策；AI 负责执行。

Halfway through, a detail caught my attention:
过程中我注意到一个细节：

> The status line shows context percentage, and triggers compaction when it hits the limit. Context percentage answers "how much room is left." But **how much information has already been lost** — nobody tells you that.
> 状态行会显示上下文占比，到一定比例就触发压缩。上下文占比是"还剩多少空间"。但**已经丢了多少信息**——没人告诉你。

Each compaction means the model discards details from earlier in the conversation → my grip on the project weakens → and I **don't know** how much.
每次压缩，模型在丢掉早期对话的细节 → 我对项目的掌控力在下降 → 但我**不知道**下降了多关键。

### Then I Looked Around / 然后我翻了一圈

Tools exist for viewing context usage (HUD progress bar), predicting upcoming compactions (cccontext), looking up historical events (ctx-inspector), and composite scoring (noctrace).
市面上有工具能看上下文用量（HUD 进度条）、能预测即将压缩（cccontext）、能回溯历史事件（ctx-inspector）、能综合打分（noctrace）。

**But none of them answers the simplest question: how many times has it been compacted?**
**但没有一个工具回答这个最简单的问题：已经被压缩了几次？**

| Tool | Shows "room left" | Shows "compaction coming" | Shows "compacted N times" |
|------|:---:|:---:|:---:|
| Claude HUD | ✅ progress bar | ❌ | ❌ |
| cccontext | ❌ | ✅ | ❌ |
| ctx-inspector | ❌ | ❌ | ⚠️ queryable history, not real-time |
| noctrace | ❌ | ❌ | ⚠️ as a scoring factor, not standalone |
| ChatGPT / Cursor / Aider | ❌ | ❌ | ❌ |

**This is the metric everyone missed.**
**这就是那个被所有人忽略的指标。**

It's the missing gauge on the dashboard — not replacing anyone, but filling the "cumulative damage log" gap.
它是现有仪表盘上缺失的一块表——不是替代谁，是补上"累计损伤记录"这个空白。

> This insight didn't come from AI. I arrived at it myself, while building the config pack.
> 这个洞察不是 AI 告诉我的。是我在做配置包的过程中自己悟出来的。

---

## 二、Why "Compaction Count"? / 为什么是"压缩次数"？

### A Natural Inverse Health Metric / 它天然就是一个反向健康指标

Context window fills up → system auto-compacts → information loss → fills up again → more loss...
上下文窗口满了 → 系统自动压缩 → 信息丢失 → 再来一轮 → 再丢：

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Original    │ ──▶ │ Compact #1   │ ──▶ │ Compact #2   │ ──▶ │ Compact #4   │
│  100% info   │     │  ~80% info   │     │  ~60% info   │     │  ~25% info   │
│  原始对话    │     │  压缩 #1      │     │  压缩 #2      │     │  压缩 #4      │
│  100% 信息   │     │  ~80% 信息   │     │  ~60% 信息   │     │  ~25% 信息   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       🟢                    🟢                    🟡                    🔴
```

**Four reasons compaction count beats context percentage for decision-making:**
**四个理由让"压缩次数"比"上下文百分比"更有决策价值：**

| Property | Compaction Count | Context Percentage |
|----------|:---:|:---:|
| Monotonic (only increases) / 单向累积 | ✅ | ❌ fluctuates / 上下波动 |
| Directly reflects info loss / 直接反映信息丢失 | ✅ | ❌ only reflects space / 只反映空间 |
| Objectively measurable (log keywords) / 客观可测 | ✅ | ⚠️ requires token parsing / 需解析 token |
| Actionable / 可转化为行动 | ✅ "2→watch, 4→reset" | ❌ "91% → now what?" |

> **You don't need users to understand compaction algorithms. Just give them a number + a color.**
> **不需要让用户看懂压缩算法。只需要给 ta 一个数字 + 一种颜色。**

---

## 三、Concept Design: One Terminal, Three States / 概念设计：同一个终端，三种状态

```
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
│  🟢 Healthy / 健康      │ │  🟡 Warning / 轻度警告   │ │  🔴 Critical / 严重警告  │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │ │  🤖 Opus 4.6            │
│  🔄 Compacted: 0        │ │  🔄 Compacted: 2        │ │  🔄 Compacted: 4        │
│  📊 Context: 23%        │ │  📊 Context: 68%        │ │  📊 Context: 91%        │
│  💰 $0.05               │ │  💰 $0.18               │ │  💰 $0.31               │
│  ───────────────────────│ │  ───────────────────────│ │  ───────────────────────│
│  ✅ Full memory         │ │  ⚠️ Partial info lost   │ │  💀 High hallucination   │
│  Model fully grasps     │ │  Watch reply quality.   │ │  Reset strongly advised! │
│  all context.           │ │  OK to continue, but    │ │  Run /reset or /rewind   │
│                         │ │  avoid complex tasks.   │ │  to an earlier node.     │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

### Design Rationale / 设计逻辑

| Decision | Rationale |
|----------|-----------|
| **Only 3 metrics exposed** / 只暴露3个指标 | Don't make users read a dashboard. Give them the critical signal. |
| **Color + text, dual channel** / 颜色+文字双通道 | Glance mode (color) and read mode (text) — two consumption speeds. |
| **Actionable advice at the bottom** / 操作建议在底部 | Don't make users do secondary judgment. Tell them what to do. |
| **Direction over precision** / 方向感优于精度 | "~60% context retained" is more useful than "exactly 63.2%". |
| **Lives in the status bar** / 放在终端状态栏 | Zero additional screen real estate. Fits existing mental models. |
| **Count, not percentage** / 次数而非百分比 | "Compacted 4 times" is more tangible than "25% context retention". |

---

## 四、Competitive Positioning: Complementary, Not Replacement / 竞争定位：不是替代，是互补

Existing context visualization tools answer different questions. Compaction count doesn't compete — it fills the **"cumulative damage log"** gap:
现有上下文可视化工具各自回答不同的问题。压缩次数不跟它们竞争，它补上的是**"已发生的损伤记录"**这个空白：

| Tool | Answers | Analogy / 类比 |
|------|---------|---------------|
| Claude HUD (progress bar) | "How much room is left?" | Fuel gauge / 油量表 |
| cccontext (prediction) | "When will compaction happen?" | Nav alert / 导航提醒 |
| ctx-inspector (lookback) | "What happened in the past?" | Dashcam / 行车记录仪 |
| noctrace (scoring) | "How healthy overall?" | Vehicle health score / 车况评分 |
| **Compaction Count (this proposal)** | **"How many times compacted?"** | **Accident log / 事故记录表** |

An ideal complete dashboard: HUD usage top-left, cccontext prediction center, compaction count top-right — **not competitors, different gauges on the same dashboard.**
一个理想化的完整仪表盘：左上角 HUD 用量，中间 cccontext 预测，右上角压缩次数累计——**它们不是竞品，是同一块仪表盘的不同仪表。**

Detailed comparison: [docs/competitive-analysis.md](docs/competitive-analysis.md)
详细对比见 [docs/competitive-analysis.md](docs/competitive-analysis.md)

---

## 五、Validation Path / 验证路径

Code implementation is not step one. Validating that the need is real — that's step one.
代码实现不是第一步。验证需求是否真实存在，才是。

### Phase 1 — Concept Validation (this repo) / 概念验证（本仓库）
- [x] ASCII terminal mockup makes the concept visible / ASCII 终端模拟图让概念可视化
- [x] Full derivation chain: pain point → metric → competitive gap → complementary positioning
- [x] Runnable monitor script framework (to prove feasibility, not for production)
- [ ] Collect real user gut-reaction feedback / 收集真实用户的直觉反馈

### Phase 2 — Community Validation / 社区验证

Pose a simple question in Claude Code / Aider / DeepSeek communities:
在 Claude Code / Aider / DeepSeek 社区发起一个简单的问题：

> "If the status bar showed 'compaction count,' would you use it to decide when to reset your session?"
> "如果终端状态栏显示'压缩次数'，你会用它来决定何时重置会话吗？"

Tally "would use it" vs. "don't care" — that's the first data point on whether the need is real.
统计"会"vs"无所谓"的比例——这是判断需求真实性的第一个数据点。

### Phase 3 — Iterate or Pivot / 迭代或转向

| Community Feedback | Action |
|--------------------|--------|
| "We have this need, already working on it" | ✅ Validated. Insight is correct. Close the proposal. |
| "Interesting, but low priority" | Gather specific concerns, iterate on the design. |
| "Not considering it" | Ask why — that's also a finding. |
| Strong community support, official silence | Consider independent implementation or PR contribution. |
| Nobody cares | **That itself is a conclusion** — document why users don't feel the pain. |

---

## 六、Why This Metric Deserves to Exist / 为什么这个指标值得存在？

**For users / 对用户：** A clear signal. No more guessing when to reset. The monthly time wasted on "AI getting dumber" now has a visible cause.
一个明确的信号，什么时候该重置不用靠猜。每月在"AI 越来越笨"上浪费的时间，现在有一个看得见的原因。

**For tool teams / 对工具团队：** Zero-cost UX improvement (the data is already in logs — just count and display). No competitor is doing this yet — differentiation.
零成本 UX 提升（日志里已有数据，只需计数并展示）。目前没有竞品做这件事——差异化竞争力。

**For the industry / 对行业：** Just as DevOps needed observability, AI-native workflows need health checks. From "magic black box" to "manageable tool."
就像 DevOps 需要可观测性一样，AI-native workflow 也需要健康检查。从"魔法黑盒"到"可管理的工具"。

---

## 七、FAQ

**Q: Isn't this just a trivial log counter? Why does it need a whole repo?**
**这不就是一个日志计数器吗，为什么需要一个仓库？**

A: The implementation is trivial — three lines of code. What's not trivial is the product judgment of *which number to surface*. Existing tools surface context percentage, token count, cost — nobody chose compaction count. The repo exists to argue for that choice, not to show off the code.

实现确实很简单——三行代码。不简单的是"在状态栏显示哪个数字"这个产品判断。现有工具都显示百分比、token 数、费用——没人选压缩次数。这个仓库在论证这个选择，不是炫代码。

**Q: Won't official tools just build this themselves, making this repo irrelevant?**
**官方工具自己加了这个功能，这个仓库不就白做了？**

A: That's the best possible outcome. The repo's value is in first identifying and articulating why this metric matters. If Anthropic or DeepSeek ships it, the insight was correct — that's a win, not a loss.

那是最好的结果。这个仓库的价值在于首先识别并论证了这个指标为什么重要。如果 Anthropic 或 DeepSeek 实现了它，说明洞察是对的——这是胜利，不是失败。

**Q: How do you know 2 compactions = warning, 4 = critical? Where do the thresholds come from?**
**你怎么知道 2 次 = 警告，4 次 = 严重？阈值从哪来的？**

A: The current thresholds are an informed starting point based on observed usage patterns, not data-proven. Phase 2 of the validation path explicitly calls for gathering real user data. A good next step would be correlating compaction count with user-initiated `/reset` behavior. The numbers will shift with data — the important thing is establishing the framework for that data to be collected.

当前阈值是基于使用观察的合理起点，不是数据验证过的。验证路径的 Phase 2 明确提出了收集真实用户数据的需求。一个好的下一步是分析压缩次数和用户主动 `/reset` 行为的相关性。数字会随数据调整——重要的是先建立收集数据的框架。

**Q: Why not just show "context retention percentage" instead of compaction count?**
**为什么不直接显示"上下文保持率"而非要用压缩次数？**

A: Retention percentage is an estimate (you don't know exactly how much information each compaction discards). Compaction count is a fact. An estimate pretends to be precise; a count is honest about what it is. Users can build their own intuition around "4 compactions = bad" faster than around "retention = 31.7%."

保持率是估算（你不知道每次压缩到底丢了什么）。压缩次数是一个事实。估算假装精确，计数诚实地就是计数。用户对"4次=危险"的直觉建立速度，比"保持率=31.7%"快得多。

**Q: Isn't this too niche? How many people even notice context compaction?**
**这个需求太小众了吧？有多少人在意上下文压缩？**

A: Every heavy user of LLM CLI tools experiences the downstream effects — they just don't attribute it to compaction. "AI is getting dumber in long sessions" is a universal complaint. The metric connects that complaint to a specific, measurable cause. Niche today, but as AI-assisted development goes mainstream, every developer will have multi-hour AI sessions.

每个重度 LLM CLI 用户都体验过它的下游影响——只是他们不知道是压缩导致的。"长会话中 AI 越来越笨"是普遍抱怨。这个指标把抱怨连接到了一个具体、可测量的原因上。今天小众，但随着 AI 辅助开发走向主流，每个开发者都会有数小时的 AI 会话。

---

## 八、Let's Make This Happen / 一起推动这件事

For tool teams, this is a **trivially cheap optimization** — compaction events are already in logs, just count and display. But the UX change is fundamental: from black box to a crack of white.
这个优化对工具团队来说**实现成本极低**——日志中已有压缩事件，只需计数并展示。但对用户体验的改变是根本性的：从黑盒到有一点白盒。

If this resonates, here's what you can do:
如果你认同这个方向，可以做的事：

- **File a Feature Request** — paste the ASCII concept mockup. It's 10x more intuitive than a text description.
- **PR to this repo** — add monitor scripts for more LLM tools (Aider, Cursor, ChatGPT Web plugin, etc.)
- **Start a discussion in your community** — V2EX, Reddit, Discord, Hacker News. Ask: "Would compaction count change when you reset?"
- **Challenge the metric** — if you think compaction count is the wrong signal, open an Issue and explain why. Being convinced otherwise is also a contribution.

For implementation details, see [CONTRIBUTING.md](CONTRIBUTING.md).
如果你想实现一个真正的 PR，见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## Repository Map / 仓库导航

```
compact-counter-concept/
├── README.md                    # 👈 You're reading it — the core proposal
├── CONTRIBUTING.md              # How to help
├── monitor.py                   # Concept-verification framework (full version)
├── compact_monitor.py           # Minimal monitor script (plug and play)
├── examples/
│   └── claude-code-hook.sh      # Claude Code PreCompact hook draft
├── tests/
│   └── test_monitor.py          # Compaction detection & state transition tests
└── docs/
    ├── idea.md                  # Core concept: compaction count = inverse health
    ├── competitive-analysis.md  # Competitive landscape: why it's not redundant
    └── architecture.md          # Design rationale: decision records
```

## License / 许可证

MIT © 2026 Tokillher

> This proposal is public. If an LLM tool team sees it and ships something similar —
> that's exactly what proving the value of an insight looks like.
>
> 这个提案是公开的。如果某个 LLM 工具团队看到并实现了类似功能——
> 那恰恰证明了这个产品洞察的价值。
