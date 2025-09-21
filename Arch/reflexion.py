# Arch/reflexion.py — Self-Refine (Reflexion): Standard attempt → Reflect once if needed (with built-in confirmation)
from __future__ import annotations
from typing import Any
import os, re

from agent_runner import AgentRunner, ModelType

# ===== Debug =====
DEBUG = os.getenv("AGENT_DEBUG", "1") not in {"0", "false", "False", ""}
def _dbg(msg: str) -> None:
    # Temporarily disabled debug prints
    # if DEBUG:
    #     print(f"[REFLEX] {msg}")
    pass

# ===== Small utils =====
def _sanitize_output(text: str) -> str:
    # Remove leaked internal thoughts or code fences if any
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # collapse whitespace
    return re.sub(r"\s+", " ", text).strip()

def _to_text(result: Any) -> str:
    # Try common attributes used by pydantic_ai result objects
    for attr in ("data", "output", "output_text", "text", "content"):
        if hasattr(result, attr):
            val = getattr(result, attr)
            if isinstance(val, str):
                return val
    # Fallback: direct str
    return str(result)

def _is_obviously_bad(text: str) -> bool:
    t = (text or "").lower().strip()
    if not t:
        return True
    for tok in ("error", "invalid", "failed", "cannot", "unknown", "not found"):
        if tok in t:
            return True
    return False

# ===== Suffixes =====
# Way B: First attempt (Standard) contains explicit confirmation after action
_STANDARD_SUFFIX = """
Use tools only; never guess names/services/entity_id.
Tools: get_entities_by_domain_tool, get_entities_details_tool, service_call_tool.

ACTION flow (MANDATORY):
1) get_entities_by_domain_tool(domain)
2) service_call_tool(domain, service, entity_id, data or {})
3) get_entities_details_tool([entity_id]) to confirm state
→ Then reply with ONE short, friendly English sentence.

STATUS flow (MANDATORY):
1) get_entities_by_domain_tool(domain)
2) get_entities_details_tool([entity_id])
→ Then reply with ONE short, friendly English sentence.

Do not reply before completing the required calls. No JSON, no tool names, no reasoning.
""".strip()

_REFLECT_SUFFIX_TEMPLATE = """
Your previous answer may be wrong or incomplete: {reason}.
Fix it with ONE corrected attempt.

Rules:
- Use tools only; never guess names/services/entity_id.
- ACTION: must call service_call_tool(...) and then confirm via get_entities_details_tool([entity_id]) before replying.
- STATUS: must call get_entities_details_tool([entity_id]) before replying.
- Reply with ONE short, friendly English sentence only. No JSON, no tool names, no reasoning.
""".strip()

# ===== Public API =====
def call_agent(user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
    """
    Reflexion (Self-Refine) — Way B:
      • Attempt #1 = STANDARD with built-in confirmation (after actions).
      • Only if the first answer looks invalid/empty → Attempt #2 (reflect & correct once).
      • No extra verification/intent classification outside the model; we trust the enforced flow.
    """
    _dbg(f"Reflexion start. text={user_text!r}")

    runner = AgentRunner()
    model = runner.available_models[model_type]()

    # -------- Attempt #1 (STANDARD with confirmation in the prompt) --------
    ag1 = runner._load_standard_agent(model)
    prompt1 = f"{user_text}\n\n{_STANDARD_SUFFIX}"
    _dbg("Attempt#1 running (STANDARD)…")
    res1 = ag1.run_sync(prompt1)
    out1 = _sanitize_output(_to_text(res1))
    _dbg(f"Attempt#1 out: {out1!r}")

    # If the first answer looks fine, return it — no second attempt.
    if not _is_obviously_bad(out1):
        return out1

    # -------- Attempt #2 (REFLECT & CORRECT once) --------
    reason = "Answer looked invalid or empty. Ensure required tool calls and (for actions) confirmation readback."
    reflect_suffix = _REFLECT_SUFFIX_TEMPLATE.format(reason=reason)
    ag2 = runner._load_reflexion_agent(model)
    prompt2 = f"{user_text}\n\nPrevious answer: {out1}\n\n{reflect_suffix}"
    _dbg("Attempt#2 running (REFLECT)…")
    res2 = ag2.run_sync(prompt2)
    out2 = _sanitize_output(_to_text(res2))
    _dbg(f"Attempt#2 out: {out2!r}")

    # Prefer the refined answer if present; otherwise fall back to attempt #1 or a safe default.
    return out2 or out1 or "Please specify the exact device."