# EXPERIMENT: Does Context Compaction Follow the Compression-Ratio Curve?

## Background

Academic research has firmly established that parameter compression (pruning, quantization) follows a peak-then-decline performance curve. The Lottery Ticket Hypothesis (ICLR 2019) proved the existence of sparse subnetworks that match or exceed full model performance. Compression scaling laws (2025) quantified the linear relationship between compression ratio and downstream task degradation.

**What's NOT studied:** Does **context summarization** (Claude Code compaction, agent session memory) follow the same pattern?

## Key Distinction

| | Parameter Compression | Context Compaction |
|---|---|---|
| What changes | Model weights | Conversation history |
| Mechanism | Pruning, quantization | LLM summarization |
| Metric | Sparsity %, bit-width | Compaction ratio |
| Peak observed | Yes (Lottery Ticket) | Unknown |
| Prior work | Extensive | None |

## Hypothesis (Revised)

Context compaction follows the same compression-ratio curve as parameter compression:

```
Performance
   │    ╭──╮         
   │   ╱    ╲        Mild compaction: remove noise → BETTER
   │  ╱      ╲       
   │ ╱        ╲      Peak: optimal information density
   │╱          ╲     
   │            ╲    Heavy compaction: lose critical context
   │            ╲    
   └──────────────────────► Compaction ratio
```

The variable is **compaction ratio** (how much of the context is summarized away), not compaction count.

## Proposed Methodology

### Setup

1. Monitor compaction events via compact-counter hooks
2. After each compaction, measure the *compaction ratio* (tokens before / tokens after)
3. Run benchmark tasks and score
4. Plot performance vs. compaction ratio (not vs. count)

### Benchmark Tasks (10 tasks, 4 categories)

**Code Understanding:**
1. Read a complex function → explain its logic and edge cases
2. Given a bug report → locate the root cause in multi-file codebase

**Reasoning:**
3. Multi-step planning problem (travel logistics with constraints)
4. Debug a logic error in a code snippet

**Factual Recall:**
5. Answer questions about content presented early in the session
6. Retrieve specific details from a long document discussed 10+ turns ago

**Creative:**
7. Generate code following complex, multi-constraint specification
8. Translate a technical document with domain-specific terminology

**Tool Use:**
9. Navigate a file tree to find specific information
10. Execute a multi-step data analysis task

### Scoring (0-5 rubric)

| Score | Criteria |
|-------|----------|
| 5 | Perfect — all constraints met, no errors |
| 4 | Minor issues only (stylistic, non-functional) |
| 3 | Functional but incomplete or with minor errors |
| 2 | Significant errors affecting correctness |
| 1 | Mostly wrong or incomplete |
| 0 | Nonsensical or completely failed |

### Procedure

```
1. Session start → compression 0, ratio 0
2. Fill context to ~70% window
3. Trigger compaction (auto or manual)
4. Record compact ratio (tokens_before / tokens_after)
5. Run all 10 benchmark tasks → score each
6. Repeat until 5+ compactions or score drops below 2/5
7. Plot mean score vs. compaction ratio (NOT count)
```

### Variables to Control

- Model (Claude Opus, GPT-5, Gemini)
- Session type (coding, analysis, creative)
- Compaction trigger (% window)
- Task difficulty baseline

## References

1. Frankle & Carbin, "The Lottery Ticket Hypothesis" (ICLR 2019)
2. "When Reasoning Meets Compression" (2025)
3. "Compression Laws for Large Language Models" (2025)
4. Iterative vs one-shot pruning comparison (arXiv:2508.13836, 2025)

## License

MIT — methodology is open. Run your own experiments.
