# compact-counter

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Research](https://img.shields.io/badge/research-papers%20cited-orange.svg)](#references)

Claude Code context compaction monitor. Tracks compaction events to help answer: **does context summarization follow the same compression-ratio curve as parameter pruning?**

## Core Insight

The "peak-then-decline" curve under compression is a **verified phenomenon** in deep learning — just not yet studied for context summarization specifically.

**What academia has proven (for parameter compression):**

```
Performance
   │    ╭──╮         Mild compression removes redundant params
   │   ╱    ╲        → implicit regularization → BETTER than baseline
   │  ╱      ╲       
   │ ╱        ╲      Peak = optimal sparsity/bit-width
   │╱          ╲     
   │            ╲    Heavy compression damages core capacity
   │            ╲    → monotonic decline, eventual collapse
   └──────────────────────► Compression ratio
```

Key finding: **the variable is compression ratio, not compression count.** Multiple rounds of mild compression can shift the peak right, but never exceed it.

## What's Unknown (Our Gap)

The academic literature covers:
- Parameter pruning (Lottery Ticket Hypothesis, ICLR 2019)
- Quantization (AWQ, GPTQ, bits-and-bytes)
- Compression scaling laws (Compression Laws for LLMs, 2025)

**Not covered:** Does *context summarization* (Claude Code compaction, agent session summarization) follow the same pattern? Context compaction is different from parameter compression — it removes tokens, not weights. But both share the same underlying principle: **redundancy removal improves, capacity removal degrades.**

This tool provides the monitoring layer to study this question across real sessions.

## How Claude Code Handles Compaction

Claude Code uses a 3-tier system:

1. **Session Memory** — Background extraction of key facts into `session_memory.md`. Incremental, no LLM cost.
2. **Full Compact** — Traditional LLM summarization. One expensive call.
3. **Circuit Breaker** — After 3 consecutive failures, compaction disabled. Worst case: 3,272 consecutive failures.

This tool tracks Full Compact events — the summarization path.

## Quick Start

```bash
cp compact-counter.py ~/.claude/scripts/
# Configure PreCompact/PostCompact/SessionStart hooks
```

## Observation Notes (DeepSeek V4, 1M context)

| Compactions | Observed Behavior | Possible Explanation |
|-------------|------------------|---------------------|
| 0 | Complete context, slower | Full information, more noise |
| 1 | Brief quality dip | First summarization removes nuance |
| 2 | Quality peak | Summarization ratio hits sweet spot |
| 3+ | Progressive decline | Excessive summarization → information loss |

**Caution:** These are anecdotal observations, not controlled experiments. The variable may be *summarization ratio* not *compaction count*. Different models/sessions will differ.

## References

### Foundational
1. Frankle & Carbin, "The Lottery Ticket Hypothesis" (ICLR 2019 Best Paper) — Dense networks contain sparse subnetworks that match/exceed original performance
2. "When Reasoning Meets Compression" (2025) — 4-bit quantization near-lossless; below 3-bit, reasoning steadily declines
3. "Compression Laws for Large Language Models" (2025) — 1000+ experiments: downstream performance decreases linearly with compression ratio
4. Iterative vs one-shot pruning comparison (arXiv:2508.13836, 2025) — Low compression: one-shot better; high compression: iterative better

### Context Management
5. Andy Liu, "How Claude Code Manages Context" (2026) — 3-tier compaction architecture
6. Claude Code Docs, "Explore the context window" — code.claude.com

## Related Tools

- [claude-context-monitor](https://github.com/avanrossum/claude-context-monitor) — Bash, warns *before* compaction. Complementary: when vs. what after.

## License

MIT
