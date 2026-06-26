# compact-counter

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Research](https://img.shields.io/badge/research-hypothesis-orange.svg)](EXPERIMENT.md)

Claude Code context compression monitor. Tracks compaction events and reveals the **multi-round compression degradation curve** — a pattern not yet studied in academic literature.

## Why

Claude Code auto-compacts sessions at ~83% context window. [Existing tools](#related-tools) tell you *when* compaction is coming. None study *what happens after multiple compressions*. This tool fills that gap.

## Core Hypothesis

LLM context compression follows a **peak-then-monotonic-decline** pattern:

```
Quality
   │    ╭──╮         
   │   ╱    ╲        Compression 0: Smart but noisy
   │  ╱      ╲       
   │ ╱        ╲      Compression 1: Brief dip (nuance lost)
   │╱          ╲     
   │            ╲    Compression 2: "回光返照" — peak (sweet spot)
   │            ╲    
   │            ╲    Compression 3+: Monotonic decline, irreversible
   └──────────────────────► Compressions
```

**Key claim:** Compression is a painkiller, not a cure. The peak at compression 2 is real but temporary — after that, the model enters irreversible decline. Existing research (RCC, ACON) treats compression as one-time; nobody has studied the multi-round curve.

Full methodology and benchmark framework in [EXPERIMENT.md](EXPERIMENT.md).

## How Claude Code Handles Compaction

Claude Code uses a 3-tier system [[1]](#references):

1. **Session Memory** — Background extraction of key facts into `session_memory.md`. Injected into system prompt. Incremental, no LLM cost per compaction.
2. **Full Compact** — Traditional LLM summarization. One expensive call when session memory isn't enough.
3. **Circuit Breaker** — After 3 consecutive failures, compaction is disabled. Worst observed case: 3,272 consecutive failures in a single session.

Our hypothesis focuses on **Full Compact** — the LLM summarization path that triggers the degradation curve.

## Quick Start

```bash
cp compact-counter.py ~/.claude/scripts/
# Configure PreCompact/PostCompact/SessionStart hooks
```

## Model-Specific Thresholds

Based on DeepSeek V4 (1M context) observation:

| Compressions | State | Behavior |
|-------------|-------|----------|
| 0 | Memory intact | Complete context, slower responses |
| 1 | Dip | First compaction removes nuance |
| 2 | **Sweet spot** | Brief resurgence — context refined |
| 3-4 | Warning | Edge information lost |
| 5+ | Degraded | Severely distorted, prefer new session |

Thresholds vary by model (window size, compaction algorithm, memory mechanics differ). This tool finds **your** model's pattern.

## Related Tools

- [claude-context-monitor](https://github.com/avanrossum/claude-context-monitor) — Bash script, warns *before* compaction triggers. Complementary: they monitor "when", we study "what happens after".
- [OpenLIT](https://openlit.io) — Full-stack LLM observability (tracing, evals, cost). Different scope: production monitoring vs. research tool.
- [Costrace](https://costrace.dev) — Cost/token/latency tracking for LLM API calls.

## References

1. Andy Liu, "How Claude Code Manages Context: A Multi-Tier Compaction System" (2026)
2. Claude Code Docs, "Explore the context window" — [code.claude.com/docs/en/context-window](https://code.claude.com/docs/en/context-window)
3. Huang et al., "Recurrent Context Compression" (ICLR 2025) — [arXiv:2406.06110](https://arxiv.org/abs/2406.06110)
4. Kang et al., "ACON: Context Compression for Long-horizon Agents" (ICLR 2026) — [arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
5. Liu et al., "Lost in the Middle" (TACL 2024) — [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)

## See Also

- [EXPERIMENT.md](EXPERIMENT.md) — Full hypothesis, methodology, benchmark design
- [open-source-flywheel](https://github.com/YuhaoLin2005/open-source-flywheel) — Methodology behind this research

## License

MIT
