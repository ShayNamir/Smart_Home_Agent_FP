# Arch/react.py — Hard-enforced ReAct with per-step timeout + no-tools planner
from __future__ import annotations
from typing import Any, Dict, Optional, List, Union
import os, re, json
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from agent_runner import AgentRunner, ModelType
from core.ha import get_entities_by_domain, get_entities_details, service_call

# === Debug ===
DEBUG = os.getenv("AGENT_DEBUG", "1") not in {"0", "false", "False", ""}
def _dbg(msg: str) -> None:
    # Temporarily disabled debug prints
    # if DEBUG:
    #     print(f"[REACT] {msg}")
    pass

# === Utils ===
def _sanitize_output(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```[\s\S]*?```", "", text)
    return re.sub(r"\s+", " ", text).strip()

def _to_text(result: Any) -> str:
    for attr in ("data", "output", "output_text", "text", "content"):
        if hasattr(result, attr):
            val = getattr(result, attr)
            if isinstance(val, str):
                return val
    return str(result)

_JSON_RE = re.compile(r"\{[\s\S]*\}")
def _extract_json(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    s2 = s.replace("```json", "").replace("```", "")
    s2 = re.sub(r"<think>[\s\S]*?</think>", "", s2, flags=re.IGNORECASE)
    m = _JSON_RE.search(s2)
    if not m:
        return None
    raw = m.group(0)
    try:
        return json.loads(raw)
    except Exception:
        fix = re.sub(r",\s*([}\]])", r"\1", raw)  # remove trailing commas
        try:
            return json.loads(fix)
        except Exception:
            return None

def _infer_intent(user_text: str) -> str:
    t = user_text.lower()
    action_tokens = ["turn on","turn off","switch on","switch off","open","close","lock","unlock","set ","increase","decrease"]
    return "action" if any(tok in t for tok in action_tokens) else "status"

def _score_candidate(name: str, entity_id: str, user_text: str) -> int:
    """Very small heuristic: boost exact/substring matches like 'kitchen', device keywords, etc."""
    u = user_text.lower()
    s = 0
    for part in re.findall(r"[a-z0-9_]+", u):
        if part and (part in (name or "").lower() or part in (entity_id or "").lower()):
            s += 2
    if "." in entity_id: s += 1
    return s

def _summarize_entities_for_obs(entities: List[Dict[str, Any]], user_text: str, top_k: int = 5) -> Dict[str, Any]:
    """Produce a compact, ranked candidate list for the planner (friendly_name + entity_id)."""
    ranked = []
    for e in entities or []:
        entity_id = e.get("entity_id") or ""
        name = e.get("name") or e.get("friendly_name") or entity_id
        ranked.append(( _score_candidate(name, entity_id, user_text), {"entity_id": entity_id, "name": name} ))
    ranked.sort(key=lambda x: x[0], reverse=True)
    candidates = [x[1] for x in ranked[:top_k]]
    return {"candidates": candidates, "count": len(entities or [])}

def _summarize_details_for_obs(details: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
    obs = []
    for d in (details or [])[:top_k]:
        obs.append({
            "entity_id": d.get("entity_id"),
            "state": d.get("state"),
            "name": d.get("attributes", {}).get("friendly_name"),
        })
    return {"details": obs, "count": len(details or [])}

# === Planner agent (no tools) ===
from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

PLANNER_SYSTEM = (
    "You are a ReAct planner. You cannot call tools. "
    "Output JSON only for the next SINGLE step."
)

PLANNER_SUFFIX = """
Choose the SINGLE next step as JSON only.
Allowed outputs (JSON only):

1) To list entities by domain:
{"tool":"get_entities_by_domain_tool","args":{"domain":"light"}}

2) To read states:
{"tool":"get_entities_details_tool","args":{"entity_ids":["light.bed_light"]}}

3) To execute an action:
{"tool":"service_call_tool","args":{"domain":"light","service":"turn_on","entity_id":"light.bed_light","data":{}}}

4) If you can answer now:
{"tool":"finish","final":"<ONE short, friendly English sentence>"}

5) If the user must clarify:
{"tool":"ask_user","message":"<ONE brief question (<=8 words)>"}

Rules:
- JSON only. No prose, no code fences, no reasoning.
- One tool per step. Pick the minimal next call that reduces uncertainty.
""".strip()

def _planner_call_with_timeout(planner: Agent, prompt: str, step_timeout: int) -> str:
    """Guarded call to planner.run_sync with per-step timeout."""
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(planner.run_sync, prompt)
        return _to_text(fut.result(timeout=step_timeout))

# === Guards ===
def _enforce_finish(intent: str, did_details: bool, did_service: bool, plan: Dict[str, Any]) -> Optional[str]:
    if plan.get("tool") != "finish":
        return None
    if intent == "action" and not did_service:
        return "For ACTION, you must call service_call_tool before finishing."
    if intent == "status" and not did_details:
        return "For STATUS, you must call get_entities_details_tool before finishing."
    return None

# === Main ===
MAX_STEPS = 3

def call_agent(user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
    _dbg(f"Start ReAct (hard). model={getattr(model_type,'name',model_type)}")
    intent = _infer_intent(user_text)
    _dbg(f"Inferred intent: {intent}")

    # Build model and a NO-TOOLS planner agent sharing the same model
    runner = AgentRunner()
    model = runner.available_models[model_type]()
    planner = Agent(
        model=model,
        system_prompt=PLANNER_SYSTEM,
        model_settings=ModelSettings(temperature=0.2)  # keep it low & stable
    )
    step_timeout = max(10, min(timeout_s, 40))  # per-step wall time

    did_service = False
    did_details = False
    transcript: List[str] = []
    last_obs: Optional[Dict[str, Any]] = None

    for step in range(1, MAX_STEPS + 1):
        # Build planner prompt with compact history/observations
        history = "No previous steps." if not transcript else "\n".join(transcript[-6:])
        obs_line = "" if not last_obs else f"\nOBS:{json.dumps(last_obs, ensure_ascii=False)}"
        planner_prompt = f"USER_REQUEST:\n{user_text}\n\nPREVIOUS:\n{history}{obs_line}\n\n{PLANNER_SUFFIX}"

        _dbg(f"Step {step}: planner call (timeout {step_timeout}s)…")
        try:
            planner_text = _planner_call_with_timeout(planner, planner_prompt, step_timeout)
        except TimeoutError:
            _dbg("Planner timeout.")
            return "Still thinking—please repeat with the exact device name."
        _dbg(f"Planner raw: {planner_text!r}")
        plan = _extract_json(planner_text)
        _dbg(f"Planner parsed: {plan}")

        if not plan or "tool" not in plan:
            return "Which device exactly? (name/room)"

        # guard finish
        guard_msg = _enforce_finish(intent, did_details, did_service, plan)
        if guard_msg:
            transcript.append(f"GUARD: {guard_msg}")
            _dbg(f"Finish blocked: {guard_msg}")
            continue

        tool = plan["tool"]

        # ask_user → short question and stop
        if tool == "ask_user":
            msg = plan.get("message") or "Which device exactly?"
            return _sanitize_output(msg)

        # finish → final message
        if tool == "finish":
            return _sanitize_output(plan.get("final") or "")

        # ==== ACTOR: execute one tool ====
        if tool == "get_entities_by_domain_tool":
            domain = (plan.get("args") or {}).get("domain") or ""
            ents = get_entities_by_domain(domain)
            obs = _summarize_entities_for_obs(ents, user_text, top_k=5)
            last_obs = obs
            transcript.append(f"ACTION:get_entities_by_domain_tool({domain!r})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            _dbg(f"Entities obs: {obs}")

        elif tool == "get_entities_details_tool":
            entity_ids = (plan.get("args") or {}).get("entity_ids") or []
            det = get_entities_details(entity_ids)
            obs = _summarize_details_for_obs(det, top_k=3)
            last_obs = obs
            did_details = True
            transcript.append(f"ACTION:get_entities_details_tool({entity_ids})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            _dbg(f"Details obs: {obs}")

        elif tool == "service_call_tool":
            args = plan.get("args") or {}
            domain = args.get("domain")
            service = args.get("service")
            entity_id = args.get("entity_id")
            data = args.get("data", {}) or {}
            call_res = service_call(domain, service, entity_id, data)
            obs = {"service_done": True, "domain": domain, "service": service, "entity_id": entity_id}
            last_obs = obs
            did_service = True
            transcript.append(f"ACTION:service_call_tool({domain},{service},{entity_id})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            _dbg(f"Service obs: {obs}")

        else:
            _dbg(f"Unknown tool: {tool}")
            return "Which device exactly? (name/room)"

    # === After MAX_STEPS fallback ===
    if intent == "action" and not did_service:
        return "I couldn’t confirm the action. Which device exactly?"
    if intent == "status" and not did_details:
        return "I couldn’t read the state. Which device exactly?"
    return "I’m not sure yet—please specify the device."