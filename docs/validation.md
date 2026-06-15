# Validation Path / 验证路径

Code implementation is not step one. Validating that the need is real — that's step one.
代码实现不是第一步。验证需求是否真实存在，才是。

## Phase 1 — Concept Validation (this repo) / 概念验证（本仓库）

- [x] Terminal mockup screenshot makes the concept visible on first glance
- [x] Full derivation chain: pain point → metric → competitive gap → complementary positioning
- [x] Runnable monitor script framework (proves feasibility, not for production)
- [x] One-liner grep command — anyone can verify compaction events exist in their own logs
- [x] **Production implementation: `compact-counter.py`** — Claude Code hook-based, validated across multiple compaction cycles
- [ ] Collect real user gut-reaction feedback

## Phase 2 — Community Validation / 社区验证

Pose a simple question in Claude Code / Aider / DeepSeek communities:

> "If the status bar showed 'compaction count,' would you use it to decide when to reset your session?"

在 Claude Code / Aider / DeepSeek 社区发起讨论：

- GitHub Discussions / Discord / Reddit
- Collect user intuition responses to the concept
- Tally "would use it" vs. "don't care" — first data point on whether the need is real

## Phase 3 — Iterate or Pivot / 迭代或转向

| Community Feedback | Action |
|--------------------|--------|
| "We have this need, already working on it" | ✅ Validated. Insight correct. Close proposal. |
| "Interesting, but low priority" | Gather specific concerns, iterate on design. |
| "Not considering it" | Ask why — also a finding. |
| Strong community support, official silence | Consider independent implementation or PR. |
| Nobody cares | **That itself is a conclusion.** Document why users don't feel the pain. |

## Production Implementation / 生产实现

`compact-counter.py` (in this repo) is the production-ready version that uses Claude Code hooks directly:
- **PreCompact**: increments counter, injects count into compaction summary
- **PostCompact**: updates completion timestamp, syncs statusline
- **SessionStart**: startup initializes, compact resumes, clear resets
- **Detection**: uses `hook_event_name` from JSON payload + regex fallback for huge PostCompact payloads
- **State**: atomic JSON persistence at `~/.claude/compact-state.json`

Integrated into [deepseek-claude-code-starter](https://github.com/YuhaoLin2005/deepseek-claude-code-starter).

## Key Principle / 核心原则

Don't commit to one direction. Design the validation so that **every outcome is a useful data point** — including "nobody cares."

不赌一个方向。设计验证路径时确保**每一种结果都是有用的数据点**——包括"没人关心"。
