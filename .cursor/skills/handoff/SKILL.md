---
name: handoff
description: Creates a clean, structured handoff document at the end of work. Use when the user says "handoff", "završi", "proglasi handoff", "wrap up", or when the task is complete and needs to be passed on.
---

# Handoff Skill

When the user requests a handoff or the work is complete, produce a clean handoff document.

## Output Format (strict)

Always respond with **only** the following structure (no extra commentary before or after):

### HANDOFF

**Status:** [Completed / Partially completed / Blocked]

**What was done:**
- ...

**Key decisions:**
- ...

**Current state:**
- Files changed / created:
- Important outputs:

**What remains:**
- ...

**Next recommended steps:**
1. ...
2. ...

**Context for next agent/human:**
- ...

**Handoff ready:** Yes

---

## Rules
- Be concise and factual.
- Never invent work that was not done.
- If something is incomplete, clearly mark it under "What remains".
- Make the handoff self-contained so another agent or human can continue without reading the full chat.
