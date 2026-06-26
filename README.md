# compact-counter

Claude Code context compression monitor. Tracks compaction events and reveals the **multi-round compression degradation curve** — a pattern not yet studied in academic literature.

## Core Hypothesis

LLM context compression follows a **peak-then-monotonic-decline** pattern, not simple linear degradation:

```
Quality
   │    ╭──╮         Compression 0: Smart but noisy
   │   ╱    ╲        
   │  ╱      ╲       Compression 1: Brief dip (nuance lost)
   │ ╱        ╲      
   │╱          ╲     Compression 2: "回光返照" — brief resurgence
   │            ╲    
   │            ╲    Compression 3+: Monotonic decline, irreversible
   │             ╲
   └──────────────────────► Compressions
```

**Key claim:** Compression is a painkiller, not a cure. After the peak at compression 2, the model enters irreversible decline. This has NOT been studied — existing research (RCC, ACON) treats compression as a one-time event.

Full hypothesis, methodology, and benchmark framework in [EXPERIMENT.md](EXPERIMENT.md).

## Model-Specific Thresholds

Based on DeepSeek V4 (1M context) observation:

| Compressions | State | Behavior |
|-------------|-------|----------|
| 0 | Memory intact | Complete context, slower responses |
| 1 | Dip | First compression removes nuance |
| 2 | **Sweet spot** | Brief resurgence — context refined, responsive |
| 3-4 | Warning | Edge information lost, verify complex tasks |
| 5+ | Degraded | Context severely distorted, prefer new session |

Thresholds vary by model (Claude/GPT/Gemini differ in window size, compression algorithm, memory mechanics). This tool helps you **find your model's pattern**, not enforce a universal standard.

## Quick Start

```bash
cp compact-counter.py ~/.claude/scripts/
# Configure PreCompact/PostCompact/SessionStart hooks
# See deepseek-claude-code-starter for full config
```

## Limitations

- Thresholds based on single-model observation (DeepSeek V4)
- Multi-session cumulative (doesn't auto-reset)
- Windows-only tested
- No auto-refresh — run manually to check

## See Also

- [EXPERIMENT.md](EXPERIMENT.md) — Full hypothesis, methodology, citations
- [deepseek-claude-code-starter](https://github.com/YuhaoLin2005/deepseek-claude-code-starter) — Parent scaffolding project
- [open-source-flywheel](https://github.com/YuhaoLin2005/open-source-flywheel) — Methodology used to develop this research

## Prior Art / Citations

- Huang et al., "Recurrent Context Compression" (ICLR 2025) — [arXiv:2406.06110](https://arxiv.org/abs/2406.06110)
- Kang et al., "ACON: Context Compression for Long-horizon Agents" (ICLR 2026) — [arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
- Liu et al., "Lost in the Middle" (TACL 2024) — [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)

## License

MIT
