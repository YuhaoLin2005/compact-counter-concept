# 邮件模板

## 标题
Feature Suggestion: Expose context compaction count to users

## 正文

Dear [Team Name],

I'm a heavy user of [Your Product] and also a product/operations intern candidate.

**Problem:** In long conversations, users have no visibility into when the model starts losing information due to context compaction. This leads to wasted tokens, increased hallucinations, and a "black box" anxiety.

**My suggestion:** Expose a simple counter – the number of times context compaction has been triggered in the current session. Display it in the status bar (for CLI) or as a small badge (for web UI).

**Why it helps:** Compaction count is an accurate, system-generated signal of health degradation. Users can decide when to reset or rewind the conversation.

I've created a concept and open-sourced it here: [Your GitHub Repo Link]

Would your team consider adding such a signal? I'm happy to provide more user scenarios.

Thank you.

[Your Name]
[Your Contact / GitHub / LinkedIn]
