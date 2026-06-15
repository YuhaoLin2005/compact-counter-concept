#!/usr/bin/env python3
"""
Compaction Counter — real-time inverse health metric for Claude Code sessions.
压缩次数实时计数器 — 让 Claude Code 状态栏能显示压缩次数。

Hooks used: PreCompact, PostCompact, SessionStart, Stop
存储：~/.claude/compact-state.json  (session_id → count + history)

Production implementation of the compact-counter-concept.
See: https://github.com/YuhaoLin2005/compact-counter-concept
"""

import sys, json, os, re
from datetime import datetime
from pathlib import Path

# Windows GBK stdout can't handle emoji — force UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

STATE_FILE = Path.home() / ".claude" / "compact-state.json"


def load_state():
    """Read the persistent state file."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {}
    except Exception:
        return {}


def save_state(state):
    """Write state atomically."""
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


def get_count(session_id, state):
    """Get compaction count for a session."""
    return state.get(session_id, {}).get("count", 0)


def increment_count(session_id, trigger, state):
    """Increment compaction count and record timestamp."""
    if session_id not in state:
        state[session_id] = {"count": 0, "history": [], "started": datetime.now().isoformat()}
    state[session_id]["count"] += 1
    state[session_id]["history"].append({
        "time": datetime.now().isoformat(),
        "trigger": trigger,
        "count": state[session_id]["count"]
    })
    return state[session_id]["count"]


def display_status(count, session_id=None):
    """Return a human-readable status string."""
    if count == 0:
        return "\033[32m[OK] 压缩 0 次 — 记忆完整\033[0m"
    elif count <= 2:
        return f"\033[33m[WARN] 压缩 {count} 次 — 部分信息丢失，注意回复质量\033[0m"
    else:
        return f"\033[31m[CRIT] 压缩 {count} 次 — 高幻觉风险，建议 /reset\033[0m"


def sync_to_statusline(session_id, count):
    """Sync compaction count to the format statusline.py reads."""
    statusline_file = Path.home() / ".claude" / ".compaction_state.json"
    try:
        existing = {}
        if statusline_file.exists():
            existing = json.loads(statusline_file.read_text(encoding="utf-8"))
        existing["compactions"] = count
        existing["last_session_id"] = session_id
        existing["updated"] = datetime.now().isoformat()
        statusline_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = statusline_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(existing, ensure_ascii=False), encoding="utf-8")
        tmp.replace(statusline_file)
    except Exception:
        pass  # Never let sync failure break the hook


def handle_precompact(payload):
    """PreCompact hook: inject compaction count into summary so it survives."""
    session_id = payload.get("session_id", "unknown")
    trigger = payload.get("trigger", "auto")

    state = load_state()
    new_count = increment_count(session_id, trigger, state)
    save_state(state)

    # Sync to statusline state file so the status bar shows correct count
    sync_to_statusline(session_id, new_count)

    status = display_status(new_count)
    status_mono = status.replace("\033[32m", "").replace("\033[0m", "").replace("\033[33m", "").replace("\033[31m", "")

    # Inject into the compaction summary so Claude remembers the count
    inject = {
        "inject_into_summary": (
            f"[COMPACTION COUNTER] This session has been compacted {new_count} time(s). "
            f"Status: {status_mono}. "
            f"Previous compactions: {' → '.join(str(h['count']) for h in state.get(session_id, {}).get('history', []))}. "
            f"Next compaction will be #{new_count + 1}."
        ),
        "extracted_data": {
            "compaction_count": new_count,
            "compaction_status": status_mono
        }
    }

    print(json.dumps(inject))


def handle_postcompact(payload):
    """PostCompact hook: update state with post-compaction info."""
    session_id = payload.get("session_id", "unknown")

    state = load_state()
    count = get_count(session_id, state)

    # Update last compaction time
    if session_id in state and state[session_id].get("history"):
        state[session_id]["history"][-1]["completed"] = datetime.now().isoformat()

    save_state(state)

    # Sync to statusline and print status
    sync_to_statusline(session_id, count)
    status = display_status(count)
    print(status)


def handle_session_start(payload):
    """SessionStart hook: report compaction status or reset counter."""
    session_id = payload.get("session_id", "unknown")
    source = payload.get("source", "startup")

    state = load_state()
    count = get_count(session_id, state)

    if source == "startup":
        # New session — initialize counter
        if session_id not in state:
            state[session_id] = {"count": 0, "history": [], "started": datetime.now().isoformat()}
            save_state(state)
        # Always sync 0 to statusline on fresh session start
        sync_to_statusline(session_id, 0)
        # Print status banner on startup
        status = display_status(0)
        print(f"\n{status}\n")
        sys.exit(0)

    elif source == "compact":
        # Session resumed after compaction — report current status
        status = display_status(count)
        for h in reversed(state.get(session_id, {}).get("history", [])):
            count_at_time = h["count"]
            trigger_at_time = h["trigger"]

        # Inject reminder into context
        if count > 0:
            print(json.dumps({
                "reminder": (
                    f"CONTEXT COMPACTION REMINDER: This session has been compacted {count} time(s). "
                    f"{'[OK] Minimal loss.' if count <= 1 else '[WARN] Some context lost — verify replies.' if count <= 2 else '[CRIT] Significant information lost — consider /reset.'}"
                )
            }))

    elif source == "clear":
        # Session was reset — reset counter
        state.pop(session_id, None)
        save_state(state)
        print("\n\033[32m[RESET] 计数器已重置 — 新对话开始\033[0m\n")
        sys.exit(0)


def handle_stop(payload):
    """Stop hook: display final compaction status."""
    session_id = payload.get("session_id", "unknown")

    state = load_state()
    count = get_count(session_id, state)

    status = display_status(count)
    print(f"\n{'='*50}")
    print(f"  {status}")
    if count > 0:
        history = state.get(session_id, {}).get("history", [])
        parts = [f"#{h['count']}({h['trigger']})" for h in history]
        print(f"  [HIST] 压缩历史: {' → '.join(parts)}")
    print(f"{'='*50}\n")


def detect_event(payload):
    """Infer hook event type from the JSON payload structure.

    Claude Code hooks receive different payload shapes:
    - PreCompact:  {session_id, trigger, hook_event_name, ...}
    - PostCompact: {session_id, hook_event_name, compact_summary, ...}
    - SessionStart:{session_id, source, hook_event_name, ...}
    - Stop:        {session_id, ...}

    Falls back to CLAUDE_HOOK_EVENT env var if set.
    """
    # Prefer explicit env var if set
    env_event = os.environ.get("CLAUDE_HOOK_EVENT", "")
    if env_event:
        return env_event

    # Prefer hook_event_name from payload (Claude Code sends this explicitly)
    if payload.get("hook_event_name"):
        return payload["hook_event_name"]

    # Infer from payload fields (fallback for older Claude Code versions)
    if not payload:
        return ""
    if "trigger" in payload:
        return "PreCompact"
    if "source" in payload:
        return "SessionStart"
    if "session_id" in payload:
        # PostCompact or Stop — Stop isn't configured for this script
        return "PostCompact"
    return ""


if __name__ == "__main__":
    # Read stdin once — all hook types receive JSON on stdin
    raw_stdin = ""
    try:
        raw_stdin = sys.stdin.read()
    except Exception:
        pass

    payload = {}
    try:
        if raw_stdin.strip():
            payload = json.loads(raw_stdin)
    except json.JSONDecodeError:
        pass

    # If JSON parsing failed (PostCompact sends huge compact_summary that may
    # break JSON), extract hook_event_name via regex as fallback.
    if not payload and raw_stdin.strip():
        m = re.search(r'"hook_event_name"\s*:\s*"([^"]*)"', raw_stdin)
        if m:
            payload = {"hook_event_name": m.group(1), "_raw": True}
            # Also try to extract session_id for state lookup
            m2 = re.search(r'"session_id"\s*:\s*"([^"]*)"', raw_stdin)
            if m2:
                payload["session_id"] = m2.group(1)

    # Determine event type
    event = detect_event(payload)

    # Fallback: try argv if still no event
    if not event and len(sys.argv) > 1:
        event = sys.argv[1]

    handlers = {
        "PreCompact": handle_precompact,
        "PostCompact": handle_postcompact,
        "SessionStart": handle_session_start,
        "Stop": handle_stop,
    }

    handler = handlers.get(event)
    if handler:
        handler(payload)
    else:
        # Unknown event — print current status (used by statusline, manual runs)
        state = load_state()
        session_id = os.environ.get("CLAUDE_SESSION_ID", "")
        count = get_count(session_id, state) if session_id else 0
        print(display_status(count))
        sys.exit(0)
