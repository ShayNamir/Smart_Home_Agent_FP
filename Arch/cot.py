# Arch/cot.py — Chain-of-Thought (CoT) with HARD enforcement:
# 1) Planner (LLM, no tools) produces a short multi-step JSON plan (+hidden thoughts).
# 2) Executor runs the exact tool steps in order (one tool per step).
# 3) Mandatory guards: ACTION must include service_call_tool; STATUS must include get_entities_details_tool.
# 4) Finalizer returns ONE short, friendly English sentence. No JSON, no tool names, no reasoning.

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import os, re, json
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from agent_runner import AgentRunner, ModelType
from core.ha import get_entities_by_domain, get_entities_details, service_call

# =============== Debug ===============
DEBUG = os.getenv("AGENT_DEBUG", "1") not in {"0", "false", "False", ""}
def _dbg(msg: str) -> None:
    # Temporarily disabled debug prints
    # if DEBUG:
    #     print(f"[COT] {msg}")
    pass

# =============== Small utils ===============
def _sanitize_output(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
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
        fix = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            return json.loads(fix)
        except Exception:
            return None

def _score_match(user_text: str, text: str) -> int:
    score = 0
    u = (user_text or "").lower()
    t = (text or "").lower()
    for part in re.findall(r"[a-z0-9_]+", u):
        if len(part) < 2:
            continue
        if part in t:
            score += 1
    return score

def _expected_on_off(user_text: str) -> Optional[str]:
    t = (user_text or "").lower()
    if "turn on" in t or "switch on" in t or "open" in t:
        return "on"
    if "turn off" in t or "switch off" in t or "close" in t:
        return "off"
    return None

def _infer_intent(user_text: str) -> str:
    t = (user_text or "").lower()
    action_tokens = ["turn on","turn off","switch on","switch off","open","close","lock","unlock","set ","increase","decrease","toggle","dim","brighten"]
    return "action" if any(tok in t for tok in action_tokens) else "status"

def _likely_domains(user_text: str, intent: str) -> List[str]:
    t = (user_text or "").lower()
    hits = []
    for dom in ["light","switch","fan","lock","cover","climate","media_player","sensor"]:
        if dom in t:
            hits.append(dom)
    if hits:
        return hits
    if intent == "action" and _expected_on_off(user_text) is not None:
        return ["light", "switch", "fan"]
    return ["light","switch","fan","lock","cover","climate","media_player","sensor"]

def _best_entity_from_candidates(user_text: str, candidates: List[Dict[str, str]]) -> Optional[str]:
    if not candidates:
        return None
    ranked: List[Tuple[int, str]] = []
    for c in candidates:
        eid = c.get("entity_id") or ""
        name = c.get("name") or ""
        txt = f"{eid} {name}"
        ranked.append((_score_match(user_text, txt), eid))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None

def _summarize_entities_for_obs(entities: List[Dict[str, Any]], user_text: str, top_k: int = 6) -> Dict[str, Any]:
    ranked: List[Tuple[int, Dict[str, str]]] = []
    for e in entities or []:
        eid = e.get("entity_id") or ""
        name = e.get("name") or e.get("friendly_name") or eid
        ranked.append((_score_match(user_text, f"{eid} {name}"), {"entity_id": eid, "name": name}))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return {"candidates": [x[1] for x in ranked[:top_k]], "count": len(entities or [])}

def _summarize_details_for_obs(details: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
    obs = []
    for d in (details or [])[:top_k]:
        obs.append({
            "entity_id": d.get("entity_id"),
            "state": d.get("state"),
            "name": d.get("attributes", {}).get("friendly_name"),
        })
    return {"details": obs, "count": len(details or [])}

def _is_obviously_bad(text: str) -> bool:
    t = (text or "").lower().strip()
    if not t:
        return True
    for tok in ("error", "invalid", "failed", "cannot", "unknown", "not found"):
        if tok in t:
            return True
    return False

# =============== CoT Planner (no tools) ===============
from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

PLANNER_SYSTEM = (
    "You are a Chain-of-Thought planner. You cannot call tools. "
    "First think briefly, then output a JSON PLAN only."
)

# We ask for 2–4 brief 'thoughts' + concrete tool 'steps' (no list_domain_services_tool).
PLAN_TEMPLATE = """
USER_REQUEST:
{user_text}

CONTEXT (compact):
- Available tools: get_entities_by_domain_tool(domain), get_entities_details_tool([entity_id]), service_call_tool(domain, service, entity_id, data or {{}})
- ACTION requires a service_call_tool before answering.
- STATUS requires get_entities_details_tool before answering.
- Use one tool per step. 2–4 steps total.

Output JSON ONLY, like:
{{
  "thoughts": ["...","..."],             // brief, will not be shown to user
  "steps": [                             // 2–4 ordered steps
    {{"tool":"get_entities_by_domain_tool","args":{{"domain":"light"}}}},
    {{"tool":"service_call_tool","args":{{"domain":"light","service":"turn_on","entity_id":"light.kitchen","data":{{}}}}}},
    {{"tool":"get_entities_details_tool","args":{{"entity_ids":["light.kitchen"]}}}}
  ],
  "final_hint": "Kitchen light is on."   // ONE short, friendly English sentence
}}
""".strip()

FINALIZER_SYSTEM = (
    "You are a concise assistant. Given the user request and observations, "
    "return ONE short, friendly English sentence. No JSON, no tool names, no reasoning."
)

def _planner_with_timeout(planner: Agent, prompt: str, timeout_s: int) -> Dict[str, Any]:
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(planner.run_sync, prompt)
        raw = _to_text(fut.result(timeout=timeout_s))
    plan = _extract_json(raw)
    return plan or {}

def _finalize_with_timeout(finalizer: Agent, prompt: str, timeout_s: int) -> str:
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(finalizer.run_sync, prompt)
        return _sanitize_output(_to_text(fut.result(timeout=timeout_s)))

# =============== Public API ===============
def call_agent(user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
    """
    CoT (hard-enforced):
      1) LLM planner produces a JSON plan with 2–4 steps (one tool per step).
      2) Executor runs steps in order, building observations.
      3) Guards ensure ACTION includes service_call_tool and STATUS includes get_entities_details_tool.
      4) Finalizer returns ONE short sentence.
    """
    _dbg(f"Start CoT. text={user_text!r}")
    intent = _infer_intent(user_text)
    _dbg(f"Inferred intent: {intent}")

    runner = AgentRunner()
    model = runner.available_models[model_type]()

    planner = Agent(
        model=model,
        system_prompt=PLANNER_SYSTEM,
        model_settings=ModelSettings(temperature=0.4),  # stable for small local models
    )

    finalizer = Agent(
        model=model,
        system_prompt=FINALIZER_SYSTEM,
        model_settings=ModelSettings(temperature=0.2),
    )

    # ---- 1) PLAN ----
    plan = _planner_with_timeout(planner, PLAN_TEMPLATE.format(user_text=user_text), timeout_s=min(60, max(20, timeout_s)))
    _dbg(f"Plan: {json.dumps({'steps': plan.get('steps', []), 'final_hint': plan.get('final_hint')}, ensure_ascii=False)}")

    steps = plan.get("steps") or []
    final_hint = plan.get("final_hint") or ""

    # Basic guard on steps length
    if not isinstance(steps, list) or not steps:
        # Minimal default plan per intent if planner failed
        steps = [{"tool":"get_entities_by_domain_tool","args":{"domain": _likely_domains(user_text, intent)[0]}}]
        if intent == "action":
            steps.append({"tool":"service_call_tool","args":{"domain":"light","service":"turn_on" if _expected_on_off(user_text)=="on" else "turn_off","entity_id":""}})
            steps.append({"tool":"get_entities_details_tool","args":{"entity_ids":[]}})
        else:
            steps.append({"tool":"get_entities_details_tool","args":{"entity_ids":[]}})

    # ---- 2) EXECUTE ----
    did_service = False
    did_details = False
    last_obs: Dict[str, Any] = {}
    transcript: List[str] = []

    def _collect_candidates_for_domain(domain: str) -> List[Dict[str, str]]:
        ents = get_entities_by_domain(domain or "")
        obs = _summarize_entities_for_obs(ents, user_text, top_k=6)
        return obs.get("candidates", [])

    for idx, item in enumerate(steps[:4]):  # cap 4 steps
        if not isinstance(item, dict) or "tool" not in item:
            continue
        tool = item["tool"]
        args = item.get("args") or {}

        if tool == "get_entities_by_domain_tool":
            domain = args.get("domain") or ""
            # If domain unspecified, pick plausible domains until one returns entities
            domains = [domain] if domain else _likely_domains(user_text, intent)
            ents = []
            used_dom = ""
            for d in domains:
                tmp = get_entities_by_domain(d)
                if tmp:
                    ents = tmp
                    used_dom = d
                    break
            obs = _summarize_entities_for_obs(ents, user_text, top_k=6)
            last_obs = obs
            transcript.append(f"ACTION:get_entities_by_domain_tool({used_dom or domain!r})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            continue

        if tool == "get_entities_details_tool":
            # If empty, try resolving from last_obs candidates
            entity_ids = args.get("entity_ids") or []
            if not entity_ids:
                entity_ids = []
                cands = (last_obs.get("candidates") if isinstance(last_obs, dict) else None) or []
                best = _best_entity_from_candidates(user_text, cands)
                if best:
                    entity_ids = [best]
            det = get_entities_details(entity_ids)
            obs = _summarize_details_for_obs(det, top_k=3)
            last_obs = obs
            did_details = True
            transcript.append(f"ACTION:get_entities_details_tool({entity_ids})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            continue

        if tool == "service_call_tool":
            # Resolve domain → candidates → best entity → service
            domain = args.get("domain")
            if not domain:
                for d in _likely_domains(user_text, intent):
                    tmp = get_entities_by_domain(d)
                    if tmp:
                        domain = d
                        last_obs = _summarize_entities_for_obs(tmp, user_text, top_k=6)
                        break
            requested_eid = args.get("entity_id")
            candidates = []
            lo = last_obs if isinstance(last_obs, dict) else {}
            if lo.get("candidates"):
                candidates = lo["candidates"]
            else:
                candidates = _collect_candidates_for_domain(domain or "")
            resolved_eid = requested_eid if requested_eid in {c.get("entity_id") for c in candidates} else _best_entity_from_candidates(user_text, candidates)
            if not resolved_eid:
                # Cannot act yet → skip this step (plan under-specified)
                transcript.append("GUARD:entity_id unresolved; skipping service_call this step.")
                continue
            service = args.get("service")
            if not service:
                exp = _expected_on_off(user_text)
                if exp == "on":
                    service = "turn_on"
                elif exp == "off":
                    service = "turn_off"
            if not domain or not service:
                transcript.append("GUARD:domain/service unresolved; skipping service_call this step.")
                continue
            _ = service_call(domain, service, resolved_eid, args.get("data") or {})
            obs = {"service_done": True, "domain": domain, "service": service, "entity_id": resolved_eid}
            last_obs = obs
            did_service = True
            transcript.append(f"ACTION:service_call_tool({domain},{service},{resolved_eid})")
            transcript.append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
            continue

        # ignore unknown tools

    # ---- 3) GUARDS (CoT compliance) ----
    if intent == "action" and not did_service:
        # If the plan failed to include/execute a service call, ask a brief clarifying question
        return "Which exact device should I control?"

    if intent == "status" and not did_details:
        return "Which device’s status should I check?"

    # ---- 4) FINALIZE ----
    # Prefer the planner's final_hint if it exists and seems sane
    if final_hint and not _is_obviously_bad(final_hint):
        return _sanitize_output(final_hint)

    # Otherwise, build a concise final message using observations
    if intent == "action":
        eid = (last_obs or {}).get("entity_id", "")
        # Try to craft a friendly short reply
        if isinstance(eid, str) and eid:
            pretty = eid.split(".")[-1].replace("_"," ").title()
            svc = (last_obs or {}).get("service","")
            if svc == "turn_on":
                return f"{pretty} turned on."
            if svc == "turn_off":
                return f"{pretty} turned off."
        return "Action completed."
    else:
        dets = (last_obs or {}).get("details") or []
        if dets:
            st = str(dets[0].get("state","")).lower()
            name = dets[0].get("name") or dets[0].get("entity_id") or "Device"
            if st:
                return f"{name} is {st}."
        # As a fallback, let the finalizer summarize concisely
        obs_str = json.dumps(last_obs or {}, ensure_ascii=False)
        final_prompt = f"User: {user_text}\nObservations: {obs_str}\nReturn one short sentence."
        try:
            return _finalize_with_timeout(finalizer, final_prompt, timeout_s=min(30, max(10, timeout_s//4)))
        except TimeoutError:
            return "Status read."