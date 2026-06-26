# EXPERIMENT: Multi-Round Compression Degradation Curve

## Hypothesis

LLM context compression follows a **peak-then-monotonic-decline** pattern, not simple linear degradation:

```
  Quality
    │  ┌──────┐
    │  │ pre  │  Smart but noisy
    │  └──┬───┘
    │     │  1st compress
    │  ┌──┴───┐
    │  │ dip  │  Brief stupidity (nuance lost)
    │  └──┬───┘
    │     │  2nd compress
    │  ┌──┴───┐
    │  │ peak │  "回光返照" — brief resurgence
    │  └──┬───┘
    │     │  3rd compress
    │     └──────►  Monotonic decline, irreversible
    │
    └─────────────────────────────────► Compressions
```

**Key claim:** Compression is not a sustainable solution for long sessions. It provides a brief resurgence (compression 2) but after that peak, the model enters irreversible monotonic decline.

## Prior Work

| Paper | Finding | Gap |
|-------|---------|-----|
| RCC (ICLR 2025) | Compression degrades performance; propose instruction reconstruction | Single compression only |
| ACON (ICLR 2026) | Agent context growth degrades reasoning; optimize compression guidelines | Single-task optimization |
| Morph (2026) | GPT-5.4 drops from 97.2% at 32K to 36.6% at 1M tokens | Tests context length, not compression rounds |

**What's missing:** No prior work studies the multi-round compression curve. All existing research treats compression as a one-time event, not a recurring session phenomenon.

## Proposed Methodology

### Setup

1. Select a model with known context window (e.g., DeepSeek V4 1M, Claude Opus 200K)
2. Prepare 10 benchmark tasks across 4 categories:
   - Code understanding (read file → explain logic)
   - Reasoning (multi-step problem solving)
   - Creative (generate content with constraints)
   - Translation (complex document translation)
3. Score each task on a 0-5 rubric for correctness, completeness, and coherence

### Procedure

```
1. Run all 10 tasks with CLEAN context (compression 0) → score
2. Fill context to ~70% window → trigger compression
3. Run all 10 tasks after compression → score
4. Repeat until 8+ compressions or output quality drops below 2/5
5. Plot mean score vs compression rounds
6. Repeat with different models for cross-model comparison
```

### Metrics

- **Mean task score** (0-5) per compression round
- **Score variance** — does the model become inconsistent?
- **Token efficiency** — tokens consumed per point of score
- **Hallucination rate** — fabricated facts per response

### Variables to Control

- Model (DeepSeek V4, Claude Opus, GPT-5, Gemini)
- Context window size
- Task type distribution
- Compression trigger threshold (50% vs 70% vs 90% window)
- Session length (short vs long)

## Reproduce

1. Clone this repo
2. Install the hook per quick-start in README
3. Run a long session, tracking compressions
4. After each compression, run the benchmark tasks
5. Record scores in `data/scores.csv`
6. Run `python analyze.py` to generate the curve

```bash
# Quick start with DeepSeek V4
cp compact-counter.py ~/.claude/scripts/
# Configure hooks → start long session → run benchmarks
python analyze.py data/scores.csv --output curve.png
```

## Related Literature

- Huang et al., "Recurrent Context Compression" (ICLR 2025) — [arXiv:2406.06110](https://arxiv.org/abs/2406.06110)
- Kang et al., "ACON: Optimizing Context Compression for Long-horizon LLM Agents" (ICLR 2026) — [arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
- Liu et al., "Lost in the Middle: How Language Models Use Long Contexts" (TACL 2024) — [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)

## License

MIT — methodology is open. Data is yours.
