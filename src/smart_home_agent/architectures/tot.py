# Arch/tot.py — Tree-of-Thoughts (ToT) for Home Assistant
# LLM plans multiple branches; actor executes exactly one tool per step; scorer prunes (beam search).
# Hardened for general homes (unknown device names) with robust entity resolution inside the actor.

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import os, re, json
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from agent_runner import AgentRunner, ModelType
from core.ha import get_entities_by_domain, get_entities_details, service_call

# ================== Debug ==================
DEBUG = os.getenv("AGENT_DEBUG", "1") not in {"0", "false", "False", ""}
def _dbg(msg: str) -> None:
    # Temporarily disabled debug prints
    # if DEBUG:
    #     print(f"[TOT] {msg}")
    pass

# Global per-step timeout (seconds) — generous for local small LLMs
PER_STEP_TIMEOUT = 150

# ================== Small utils ==================
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

_JSON_RE = re.compile(r"\{[\s\S]*\}|\[[\s\S]*\]")
def _extract_json(s: str) -> Optional[Any]:
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
    """Token overlap score (simple, fast)."""
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
    """Return plausible domains ordered by likelihood (for generic homes)."""
    t = (user_text or "").lower()
    hits = []
    for dom in ["light","switch","fan","lock","cover","climate","media_player","sensor"]:
        if dom in t:
            hits.append(dom)
    if hits:
        return hits
    if intent == "action":
        # For generic on/off phrasing prefer light→switch→fan
        if _expected_on_off(user_text) is not None:
            return ["light", "switch", "fan"]
    return ["light", "switch", "fan", "lock", "cover", "climate", "media_player", "sensor"]

def _normalize_name(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("-", " ").replace(".", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _best_entity_from_candidates(user_text: str, candidates: List[Dict[str, str]]) -> Optional[str]:
    """Pick best entity_id from a list of {'entity_id','name'} by textual fit."""
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

# ================== Planner agent (NO tools) ==================
from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings

PLANNER_SYSTEM = (
    "You are a Tree-of-Thoughts planner. You cannot call tools. "
    "At each depth, propose up to K distinct next steps as JSON only."
)

PLANNER_SUFFIX_TEMPLATE = """
USER_REQUEST:
{user_text}

PREVIOUS (compact transcript):
{history}

OBS (last observation, optional):
{obs}

Propose up to {k} DISTINCT next steps as a JSON ARRAY. Each item must be ONE of:

1) List entities by domain:
{{"tool":"get_entities_by_domain_tool","args":{{"domain":"light"}}}}

2) Read states:
{{"tool":"get_entities_details_tool","args":{{"entity_ids":["light.bed_light"]}}}}

3) Execute an action:
{{"tool":"service_call_tool","args":{{"domain":"light","service":"turn_on","entity_id":"light.bed_light","data":{{}}}}}}

4) If you can answer now:
{{"tool":"finish","final":"<ONE short, friendly English sentence>"}}

5) If the user must clarify:
{{"tool":"ask_user","message":"<ONE brief question (<=8 words)>"}}  // Use sparingly.

Rules:
- JSON array ONLY. No prose, no code fences, no reasoning.
- One tool per item. Items MUST be distinct and plausible.
- Prefer minimal steps that reduce uncertainty. Avoid redundant or identical items.
""".strip()

# Replace the existing function
def _planner_call_with_timeout(planner: Agent, prompt: str, step_timeout: int) -> str:
    ex = ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(planner.run_sync, prompt)
    try:
        raw = _to_text(fut.result(timeout=step_timeout))
        ex.shutdown(wait=False, cancel_futures=True)
        return raw
    except TimeoutError:
        _dbg(f"Planner watchdog timeout after {step_timeout}s; continuing.")
        # Don't wait for full thread shutdown to avoid getting stuck
        ex.shutdown(wait=False, cancel_futures=True)
        # Agreed signal for timeout
        return "__TIMEOUT__"
    except Exception as e:
        ex.shutdown(wait=False, cancel_futures=True)
        raise

# ================== Guards & scoring ==================
def _finish_guard(intent: str, did_details: bool, did_service: bool, plan_item: Dict[str, Any]) -> Optional[str]:
    if plan_item.get("tool") != "finish":
        return None
    if intent == "action" and not did_service:
        return "For ACTION, you must call service_call_tool before finishing."
    if intent == "status" and not did_details:
        return "For STATUS, you must call get_entities_details_tool before finishing."
    return None

def _score_node(intent: str, node: Dict[str, Any], user_text: str) -> float:
    transcript_str = " ".join(node.get("transcript", []))
    obs_str = json.dumps(node.get("last_obs", {}), ensure_ascii=False)
    s = 0.0
    s += 0.5 * _score_match(user_text, transcript_str + " " + obs_str)
    if intent == "action" and node.get("did_service"):
        s += 4.0
    if intent == "status" and node.get("did_details"):
        s += 3.0
    depth = node.get("depth", 0)
    s -= 0.25 * depth
    # Prefer nodes that already gathered candidates when acting
    if intent == "action" and node.get("last_obs", {}).get("candidates"):
        s += 0.6
    return s

# ================== Main ToT search ==================
MAX_DEPTH_DEFAULT = 3

def call_agent(
    user_text: str,
    model_type: ModelType,
    timeout_s: int = 180,          # overall hint; per-step timeout is PER_STEP_TIMEOUT (150s)
    beam_size: int = 2,
    k_per_node: int = 3,
    max_depth: int = MAX_DEPTH_DEFAULT,
    planner_temperature: float = 0.4,   # stable for local 4B
) -> str:
    """
    Tree-of-Thoughts:
      • Planner (LLM) proposes up to K steps per depth (JSON only).
      • Actor executes ONE tool per candidate, records observation.
      • Scorer ranks branches; beam search keeps top-N.
      • Guards: cannot FINISH before required tool (service_call for ACTION / details for STATUS).
      • Robust entity resolution: if planner proposes unknown entity_id, actor gathers domain entities and/or
        resolves best match from candidates (works across arbitrary home names).
      • ask_user does NOT end immediately; considered a low-priority branch.
    """
    _dbg(f"Start ToT. model={getattr(model_type,'name',model_type)} depth≤{max_depth} beam={beam_size} K={k_per_node}")
    intent = _infer_intent(user_text)
    _dbg(f"Inferred intent: {intent}")

    # Planner (no tools)
    runner = AgentRunner()
    model = runner.available_models[model_type]()
    planner = Agent(
        model=model,
        system_prompt=PLANNER_SYSTEM,
        model_settings=ModelSettings(temperature=planner_temperature),
    )
    per_call_timeout = PER_STEP_TIMEOUT  # 150s

    # Node structure: transcript, last_obs, did_service, did_details, depth
    root = {"transcript": [], "last_obs": None, "did_service": False, "did_details": False, "depth": 0}
    frontier: List[Dict[str, Any]] = [root]

    for depth in range(1, max_depth + 1):
        _dbg(f"Depth {depth}: expanding {len(frontier)} nodes")
        candidates_next: List[Dict[str, Any]] = []

        for node_idx, node in enumerate(frontier):
            history = "\n".join(node["transcript"][-8:]) if node["transcript"] else "No previous steps."
            obs_line = json.dumps(node["last_obs"], ensure_ascii=False) if node["last_obs"] else "None"
            prompt = PLANNER_SUFFIX_TEMPLATE.format(
                user_text=user_text, history=history, obs=obs_line, k=k_per_node
            )

            # Planner → K candidates (LLM-only)
            raw = _planner_call_with_timeout(planner, prompt, per_call_timeout)

            if raw == "__TIMEOUT__":
                _dbg("Planner timeout; enqueueing low-priority ask_user branch.")
                plans = [{"tool": "ask_user", "message": "Which device exactly?"}]
            else:
                _dbg(f"Planner raw (node {node_idx}): {raw!r}")
                plans = _extract_json(raw)
                if not isinstance(plans, list):
                    plans = [plans] if isinstance(plans, dict) else []
                if not plans:
                    _dbg("Planner returned no valid candidates; skipping node.")
                    continue

            # Filter invalid + guards, and sort by action-priority to prefer operative branches
            filtered: List[Dict[str, Any]] = []
            seen = set()
            for item in plans[:k_per_node]:
                if not isinstance(item, dict) or "tool" not in item:
                    continue
                key = json.dumps(item, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                guard = _finish_guard(intent, node["did_details"], node["did_service"], item)
                if guard:
                    # Convert to guidance note in the transcript
                    child = {**node}
                    child["transcript"] = node["transcript"] + [f"GUARD:{guard}"]
                    child["depth"] = depth
                    candidates_next.append(child)
                    continue
                filtered.append(item)

            if not filtered:
                continue

            # Prioritize operative tools over ask_user
            priority = {"service_call_tool": 0, "get_entities_details_tool": 1,
                        "get_entities_by_domain_tool": 2, "finish": 3, "ask_user": 4}
            filtered.sort(key=lambda it: priority.get(it.get("tool",""), 5))

            # === Actor: execute ONE tool per candidate ===
            for item in filtered[:k_per_node]:
                tool = item["tool"]
                args = item.get("args") or {}
                child = {
                    "transcript": list(node["transcript"]),
                    "last_obs": None,
                    "did_service": node["did_service"],
                    "did_details": node["did_details"],
                    "depth": depth,
                }

                if tool == "ask_user":
                    # Do NOT return immediately. Keep as branch with low priority.
                    msg = args.get("message") or item.get("message") or "Which device exactly?"
                    child["last_obs"] = {"message": "ask_user", "text": msg}
                    child["transcript"].append(f"ASK:{msg}")
                    candidates_next.append(child)
                    continue

                if tool == "finish":
                    # Allowed only if guards passed (already checked)
                    final = _sanitize_output(item.get("final") or "")
                    return final or "Done."

                if tool == "get_entities_by_domain_tool":
                    domain = (args.get("domain") or "")
                    # If planner didn't specify a domain, try likely ones sequentially; use first that returns entities.
                    domains_to_try = [domain] if domain else _likely_domains(user_text, intent)
                    ents: List[Dict[str, Any]] = []
                    for d in domains_to_try:
                        if d is None:
                            continue
                        tmp = get_entities_by_domain(d)
                        if tmp:
                            domain = d
                            ents = tmp
                            break
                    # Build observation
                    obs = _summarize_entities_for_obs(ents, user_text, top_k=6)
                    child["last_obs"] = obs
                    child["transcript"].append(f"ACTION:get_entities_by_domain_tool({domain!r})")
                    child["transcript"].append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
                    candidates_next.append(child)
                    continue

                if tool == "get_entities_details_tool":
                    entity_ids = args.get("entity_ids") or []
                    det = get_entities_details(entity_ids)
                    obs = _summarize_details_for_obs(det, top_k=3)
                    child["last_obs"] = obs
                    child["did_details"] = True
                    child["transcript"].append(f"ACTION:get_entities_details_tool({entity_ids})")
                    child["transcript"].append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
                    candidates_next.append(child)
                    continue

                if tool == "service_call_tool":
                    # Robust entity resolution for general homes:
                    # 1) Domain: use provided or infer plausible domains and pick those with entities.
                    domain = args.get("domain")
                    if not domain:
                        for d in _likely_domains(user_text, intent):
                            tmp = get_entities_by_domain(d)
                            if tmp:
                                domain = d
                                # Store candidates in last_obs so we can resolve names
                                child["last_obs"] = _summarize_entities_for_obs(tmp, user_text, top_k=6)
                                break
                    # 2) Entity id: if provided but not known, or missing — resolve from last_obs candidates
                    requested_eid = args.get("entity_id")
                    resolved_eid = requested_eid

                    # Gather candidates to resolve against (SAFE for None)
                    candidates = []
                    child_obs = child.get("last_obs") or {}
                    if child_obs.get("candidates"):
                        candidates = child_obs["candidates"]
                    else:
                        node_obs = node.get("last_obs") or {}
                        if node_obs.get("candidates"):
                            candidates = node_obs["candidates"]
                        else:
                            # If we still have nothing, fetch domain entities now
                            ents = get_entities_by_domain(domain or "")
                            child["last_obs"] = _summarize_entities_for_obs(ents, user_text, top_k=6)
                            candidates = child["last_obs"]["candidates"]

                    # If requested_eid not in candidates, try best textual match
                    known_ids = {c.get("entity_id") for c in (candidates or [])}
                    if not resolved_eid or (resolved_eid not in known_ids):
                        resolved_eid = _best_entity_from_candidates(user_text, candidates)

                    # If still none — we cannot safely act yet; convert this step to an entity listing observation
                    if not resolved_eid:
                        child["transcript"].append("GUARD:entity_id unclear; listing candidates first.")
                        # Re-run listing to enrich obs (keeps one-tool-per-step discipline)
                        ents = get_entities_by_domain(domain or "")
                        obs = _summarize_entities_for_obs(ents, user_text, top_k=6)
                        child["last_obs"] = obs
                        child["transcript"].append(f"ACTION:get_entities_by_domain_tool({domain!r})")
                        child["transcript"].append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
                        candidates_next.append(child)
                        continue

                    # 3) Service: infer on/off if not provided (general homes)
                    service = args.get("service")
                    if not service:
                        exp = _expected_on_off(user_text)
                        if exp == "on":
                            service = "turn_on"
                        elif exp == "off":
                            service = "turn_off"

                    if not domain or not service:
                        # Can't act without domain or service; ask a brief clarification
                        msg = "Which device and action exactly?"
                        child["last_obs"] = {"message": "ask_user", "text": msg}
                        child["transcript"].append(f"ASK:{msg}")
                        candidates_next.append(child)
                        continue

                    # Execute
                    _ = service_call(domain, service, resolved_eid, args.get("data") or {})
                    obs = {"service_done": True, "domain": domain, "service": service, "entity_id": resolved_eid}
                    child["last_obs"] = obs
                    child["did_service"] = True
                    child["transcript"].append(f"ACTION:service_call_tool({domain},{service},{resolved_eid})")
                    child["transcript"].append(f"OBS:{json.dumps(obs, ensure_ascii=False)}")
                    candidates_next.append(child)
                    continue

                _dbg(f"Unknown tool in plan: {tool}")

        if not candidates_next:
            _dbg("No candidates to expand; stopping.")
            break

        # === Rank & prune (beam search) ===
        scored = [( _score_node(intent, n, user_text), n) for n in candidates_next]
        scored.sort(key=lambda x: x[0], reverse=True)
        frontier = [n for _, n in scored[:max(1, beam_size)]]
        _dbg(f"Kept {len(frontier)} nodes (scores: {[round(s,2) for s,_ in scored[:beam_size]]})")

        # Early FINISH try if we already satisfied the guard condition
        for node in frontier:
            if (intent == "action" and node.get("did_service")) or (intent == "status" and node.get("did_details")):
                history = "\n".join(node["transcript"][-8:]) if node["transcript"] else "No previous steps."
                obs_line = json.dumps(node["last_obs"], ensure_ascii=False) if node["last_obs"] else "None"
                finish_prompt = (
                    f"{PLANNER_SYSTEM}\n"
                    "Now output a JSON finish ONLY if you can.\n"
                    "Example: {\"tool\":\"finish\",\"final\":\"<ONE short, friendly English sentence>\"}\n\n"
                    f"USER_REQUEST:\n{user_text}\n\nPREVIOUS:\n{history}\n\nOBS:{obs_line}\n"
                )
                try:
                    raw = _planner_call_with_timeout(planner, finish_prompt, per_call_timeout)
                    plan = _extract_json(raw)
                    if isinstance(plan, dict) and plan.get("tool") == "finish":
                        final = _sanitize_output(plan.get("final") or "")
                        if final:
                            _dbg("Early FINISH accepted.")
                            return final
                except TimeoutError:
                    _dbg("Finish planner timeout; continuing search.")

    # ===== Fallback if no FINISH at all =====
    # Choose best node and craft a safe single-sentence reply
    if frontier:
        best = max(frontier, key=lambda n: _score_node(_infer_intent(user_text), n, user_text))
        if _infer_intent(user_text) == "action" and best.get("did_service"):
            obs = best.get("last_obs") or {}
            eid = obs.get("entity_id") or "Device"
            # Try to make a friendly generic line
            return f"{_sanitize_output(eid).split('.')[-1].replace('_',' ').title()} turned on." if "turn_on" in str(obs) else "Action completed."
        if _infer_intent(user_text) == "status" and best.get("did_details"):
            dets = (best.get("last_obs", {}) or {}).get("details") or []
            if dets:
                st = str(dets[0].get("state","")).lower()
                name = dets[0].get("name") or dets[0].get("entity_id") or "Device"
                if st:
                    return f"{name} is {st}."
            return "Status read."
    return "I’m not sure yet—please specify the device."