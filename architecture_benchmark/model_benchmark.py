# model_bench/model_benchmark.py — Model benchmark runner for comparing different local models
from __future__ import annotations

# --- Make project root importable ---
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]  # points to .../Smart_Home_Agent_FP
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---- stdlib imports ----
import csv, sys
csv.field_size_limit(sys.maxsize)  # allow very large CSV fields (responses, logs)
import os
import time
import datetime as dt
from typing import Dict, List, Tuple, Optional
from contextlib import redirect_stdout
import io

# ---- third-party ----
import pandas as pd  # requires: pandas, openpyxl

# ---- project imports ----
from agent_runner import AgentRunner, ModelType
from core.ha import get_entities_by_domain, get_entities_details, service_call

try:
    # when running as module: python -m model_bench.model_benchmark
    from .benchmark_commands import BENCHMARK_TESTS, build_entity_map
except ImportError:
    # when running this file directly
    from benchmark_commands import BENCHMARK_TESTS, build_entity_map

# -------------------------
# Paths & constants
# -------------------------
RESULTS_DIR = "/Users/shaynamir/Library/CloudStorage/OneDrive-ArielUniversity/לימודים/קורסים/פרויקט גמר/Smart_Home_Agent_FP/architecture_benchmark/bench_results"

# Available models for testing
AVAILABLE_MODELS = {
    "phi3:mini": ModelType.OLLAMA_PHI3_MINI,
    "llama3.2": ModelType.OLLAMA_LLAMA3_2,
    "mistral": ModelType.OLLAMA_MISTRAL,
    "qwen3:4b": ModelType.OLLAMA_QWEN3_4B,
    "gemma3:4b": ModelType.OLLAMA_GEMMA3_4B,
    "deepseek-r1:1.5b": ModelType.OLLAMA_DEEPSEEK_R1,
}

REPEATS = 1
CHECKPOINT_CSV = os.path.join(RESULTS_DIR, "model_bench_live.csv")

# Timing guards for HA state stabilization
WAIT_AFTER_SETUP = 0.0
POST_ACTION_WAIT = 0.0

PROFILE_DEFAULT = "core"  # default profile if user just presses Enter

# -------------------------
# Helpers
# -------------------------
def _safe_state(entity_id: str) -> str:
    """Return HA state string or 'not_found'."""
    try:
        det = get_entities_details([entity_id]) or []
        if not det:
            return "not_found"
        return str(det[0].get("state", "unknown"))
    except Exception:
        return "not_found"

def _expected_states_for_action(action: str) -> Tuple[str, str]:
    """(exp_init, exp_fin) for common actions."""
    a = (action or "").lower()
    if a in ("turn_on", "on"):
        return ("off", "on")
    if a in ("turn_off", "off"):
        return ("on", "off")
    if a == "lock":
        return ("unlocked", "locked")
    if a == "unlock":
        return ("locked", "unlocked")
    return ("n/a", "n/a")

def _force_state(domain: str, entity_id: str, desired_state: str) -> None:
    """
    Deterministically set device state before test.
    light/switch/fan: on/off -> turn_on/turn_off
    lock: locked/unlocked -> lock/unlock
    """
    d = (domain or "").lower()
    s = (desired_state or "").lower()

    if d in ("light", "switch", "fan"):
        if s == "on":
            service_call(d, "turn_on", entity_id, {})
        elif s == "off":
            service_call(d, "turn_off", entity_id, {})
        return

    if d == "lock":
        if s == "locked":
            service_call(d, "lock", entity_id, {})
        elif s == "unlocked":
            service_call(d, "unlock", entity_id, {})
        return

def _likely_domains_from_text(command: str) -> List[str]:
    t = (command or "").lower()
    hits = [dom for dom in ["light", "switch", "fan", "lock", "cover", "climate", "media_player", "sensor"] if dom in t]
    if hits:
        return hits
    if any(x in t for x in ["turn on", "switch on", "turn off", "switch off", "activate", "deactivate"]):
        return ["light", "switch", "fan"]
    return ["light", "switch", "fan", "lock"]

def _resolve_entity(domain: str, friendly: str, entity_map: Dict[str, Dict[str, str]]) -> Optional[str]:
    """Resolve entity_id via manual map first, fallback to fuzzy match in HA list."""
    d = (domain or "").lower()
    if d in entity_map and friendly in entity_map[d]:
        return entity_map[d][friendly]

    # Fallback: pick best match from HA
    try:
        ents = get_entities_by_domain(d) or []
        target = (friendly or "").lower()

        def score(e):
            name = (e.get("name") or e.get("friendly_name") or e.get("entity_id") or "").lower()
            eid  = (e.get("entity_id") or "").lower()
            sc = 0
            for tok in target.split():
                if tok in name or tok in eid:
                    sc += 1
            return sc

        ents = sorted(ents, key=score, reverse=True)
        return ents[0]["entity_id"] if ents else None
    except Exception:
        return None

def _timestamped_filename(prefix: str = "model_bench") -> str:
    now = dt.datetime.now().strftime("%Y%m%d_%H%M")
    return f"{prefix}_{now}.xlsx"

# -------------------------
# Test selection profiles
# -------------------------
def _pick_quota_preserve_order(tests: List[dict], limit: int) -> List[dict]:
    """Pick first 'limit' tests preserving original order (no dups by command+category)."""
    seen = set()
    out = []
    for t in tests:
        key = (t.get("command",""), t.get("category",""))
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
        if len(out) >= limit:
            break
    return out

def select_tests_profile(profile: str) -> List[Dict[str, str]]:
    """
    Profiles:
      - 'long'  : all non-error tests (full benchmark).
      - 'core'  : ~60 tests (15 per domain x 4 domains).
      - 'lite'  : ~36 tests (9 per domain x 4 domains).
      - 'micro' : ~18 tests (≈4-5 per domain).
    """
    profile = (profile or "").strip().lower() or PROFILE_DEFAULT
    include_cats = {"action", "status"}  # Skip error tests for model comparison
    base = [t for t in BENCHMARK_TESTS if (t.get("category","").lower() in include_cats)]

    if profile == "long":
        return base

    # Domains to cover in profile subsets
    domains = ["light", "switch", "fan", "lock"]

    if profile == "core":
        # 15 per domain: action 8 + status 7
        per_dom = {"action": 8, "status": 7}
    elif profile == "lite":
        # 9 per domain: action 5 + status 4
        per_dom = {"action": 5, "status": 4}
    elif profile == "micro":
        # ~18 total: action 3 + status 2 per domain (≈5 x 4 = 20; in practice if missing just less)
        per_dom = {"action": 3, "status": 2}
    else:
        # fallback to core
        per_dom = {"action": 8, "status": 7}

    selected: List[Dict[str, str]] = []
    for dom in domains:
        dom_tests = [t for t in base if (t.get("domain","").lower() == dom)]
        for cat, lim in per_dom.items():
            pool = [t for t in dom_tests if (t.get("category","").lower() == cat)]
            chosen = _pick_quota_preserve_order(pool, lim)
            selected.extend(chosen)

    return selected

# -------------------------
# Model Benchmark Runner
# -------------------------
class ModelBenchmark:
    COLUMNS = [
        "model",
        "command",
        "category",
        "response",
        "run time",
        "exp init state",
        "exp fin state",
        "act init state",
        "act fin state",
    ]

    def __init__(self, results_dir: str = RESULTS_DIR, repeats: int = REPEATS):
        self.results_dir = results_dir
        self.repeats = max(1, int(repeats))
        os.makedirs(self.results_dir, exist_ok=True)
        self.runner = AgentRunner()
        self.entity_map = build_entity_map()  # from benchmark_commands.py

    # ---- Core row execution ----
    def _run_action_test(self, model_name: str, test: Dict[str, str]) -> Dict[str, str]:
        domain = test["domain"]
        device = test["device"]
        cmd    = test["command"]
        action = test.get("action", "")
        exp_init, exp_fin = _expected_states_for_action(action)

        entity_id = _resolve_entity(domain, device, self.entity_map)
        if not entity_id:
            start = time.perf_counter()
            resp = self.runner.run("standard", cmd, AVAILABLE_MODELS[model_name])
            dur  = time.perf_counter() - start
            return {
                "model": model_name,
                "command": cmd,
                "category": "action",
                "response": resp,
                "run time": f"{dur:.2f}",
                "exp init state": exp_init,
                "exp fin state": exp_fin,
                "act init state": "not_found",
                "act fin state": "not_found",
            }

        if exp_init != "n/a":
            _force_state(domain, entity_id, exp_init)
            if WAIT_AFTER_SETUP > 0: time.sleep(WAIT_AFTER_SETUP)

        act_init = _safe_state(entity_id)

        start = time.perf_counter()
        resp = self.runner.run("standard", cmd, AVAILABLE_MODELS[model_name])
        dur  = time.perf_counter() - start

        if POST_ACTION_WAIT > 0: time.sleep(POST_ACTION_WAIT)
        act_fin = _safe_state(entity_id)

        return {
            "model": model_name,
            "command": cmd,
            "category": "action",
            "response": resp,
            "run time": f"{dur:.2f}",
            "exp init state": exp_init,
            "exp fin state": exp_fin,
            "act init state": act_init,
            "act fin state": act_fin,
        }

    def _run_status_test(self, model_name: str, test: Dict[str, str]) -> Dict[str, str]:
        domain = test["domain"]
        device = test["device"]
        cmd    = test["command"]

        entity_id = _resolve_entity(domain, device, self.entity_map)
        act_init = _safe_state(entity_id) if entity_id else "not_found"

        start = time.perf_counter()
        resp = self.runner.run("standard", cmd, AVAILABLE_MODELS[model_name])
        dur  = time.perf_counter() - start

        act_fin = _safe_state(entity_id) if entity_id else "not_found"

        return {
            "model": model_name,
            "command": cmd,
            "category": "status",
            "response": resp,
            "run time": f"{dur:.2f}",
            "exp init state": "n/a",
            "exp fin state": "n/a",
            "act init state": act_init,
            "act fin state": act_fin,
        }

    def _run_single(self, model_name: str, test: Dict[str, str]) -> Dict[str, str]:
        cat = test["category"]
        if cat == "action":
            return self._run_action_test(model_name, test)
        if cat == "status":
            return self._run_status_test(model_name, test)
        # Skip error tests for model comparison
        return {
            "model": model_name,
            "command": test.get("command", ""),
            "category": cat,
            "response": "SKIPPED",
            "run time": "0.00",
            "exp init state": "n/a",
            "exp fin state": "n/a",
            "act init state": "n/a",
            "act fin state": "n/a",
        }

    def _load_done_keys(self) -> set:
        done_keys = set()
        if os.path.exists(CHECKPOINT_CSV):
            try:
                with open(CHECKPOINT_CSV, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        done_keys.add((r.get("model",""), r.get("command",""), r.get("category","")))
            except csv.Error:
                # fallback via pandas (no field-size limit)
                df = pd.read_csv(CHECKPOINT_CSV, engine="python")
                for _, r in df.iterrows():
                    done_keys.add((str(r.get("model","")), str(r.get("command","")), str(r.get("category",""))))
        return done_keys

    def run_tests(self, tests: List[Dict[str, str]], models: List[str]) -> str:
        rows: List[Dict[str, str]] = []

        done_keys = self._load_done_keys()
        print(f"[MODEL_BENCH] Resuming: found {len(done_keys)} completed rows in checkpoint.")

        # compute total remaining for progress display
        remaining = []
        for model in models:
            for test in tests:
                key = (model, test.get("command",""), test.get("category",""))
                for _ in range(self.repeats):
                    if key not in done_keys:
                        remaining.append(key)
        total_remaining = len(remaining)
        idx = 0

        for model in models:
            print(f"[MODEL_BENCH] Running model: {model} ({len(tests)} tests x {self.repeats} repeats)")
            for test in tests:
                cmd = test.get("command", "")
                cat = test.get("category", "")
                key = (model, cmd, cat)

                for _ in range(self.repeats):
                    if key in done_keys:
                        continue

                    idx += 1
                    print(f"Test {idx}/{total_remaining} {model}: {cmd}")
                    try:
                        row = self._run_single(model, test)
                    except Exception as e:
                        row = {
                            "model": model,
                            "command": cmd,
                            "category": cat,
                            "response": f"ERROR: {e}",
                            "run time": "0.00",
                            "exp init state": "n/a",
                            "exp fin state": "n/a",
                            "act init state": "n/a",
                            "act fin state": "n/a",
                        }

                    rows.append(row)
                    # --- append to checkpoint immediately ---
                    write_header = not os.path.exists(CHECKPOINT_CSV)
                    with open(CHECKPOINT_CSV, "a", encoding="utf-8", newline="") as f:
                        w = csv.DictWriter(f, fieldnames=self.COLUMNS)
                        if write_header:
                            w.writeheader()
                        w.writerow(row)
                    done_keys.add(key)

        # === Save Excel with comprehensive analysis ===
        filename = _timestamped_filename(prefix="model_bench")
        out_path = os.path.join(self.results_dir, filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # Load all historical rows from checkpoint (combined) + new rows (this run)
        try:
            df_all = pd.read_csv(CHECKPOINT_CSV, engine="python")
        except Exception:
            df_all = pd.DataFrame(columns=self.COLUMNS)

        df_new = pd.DataFrame(rows, columns=self.COLUMNS)

        with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
            # Sheet 1: ALL results (historical + current)
            df_all.to_excel(writer, index=False, sheet_name="All Results")
            
            # Sheet 2: only rows created in THIS run
            df_new.to_excel(writer, index=False, sheet_name="Current Run")

            # Sheet 3: Model comparison summary
            if not df_all.empty and "run time" in df_all.columns:
                tmp = df_all.copy()
                tmp["run time"] = pd.to_numeric(tmp["run time"], errors="coerce")
                
                # Model performance summary
                model_summary = tmp.groupby("model").agg({
                    "run time": ["count", "mean", "median", "min", "max"],
                    "command": "count"
                }).round(2)
                model_summary.columns = ["Total Tests", "Avg Time", "Median Time", "Min Time", "Max Time", "Command Count"]
                model_summary.to_excel(writer, sheet_name="Model Summary")

                # Category analysis by model
                category_analysis = tmp.groupby(["model", "category"]).agg({
                    "run time": ["count", "mean"],
                    "command": "count"
                }).round(2)
                category_analysis.columns = ["Test Count", "Avg Time", "Command Count"]
                category_analysis.to_excel(writer, sheet_name="Category Analysis")

        print(f"[MODEL_BENCH] Saved results to: {out_path}")
        return out_path

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Profile choice (default core). Press Enter to accept CORE quickly.
    choice = input("Profile? [core|lite|micro|long] (default core): ").strip().lower()
    profile = choice or PROFILE_DEFAULT

    # Model selection
    print(f"Available models: {list(AVAILABLE_MODELS.keys())}")
    model_choice = input("Models? [all|custom csv] (default all): ").strip().lower()
    if model_choice == "all" or not model_choice:
        models = list(AVAILABLE_MODELS.keys())
    elif model_choice.startswith("custom"):
        # e.g., "custom phi3:mini,llama3.2"
        parts = model_choice.replace("custom","").strip().strip(":, ")
        models = [m.strip() for m in parts.split(",") if m.strip()]
        # Validate models exist
        models = [m for m in models if m in AVAILABLE_MODELS]
        if not models:
            print("No valid models specified, using all models")
            models = list(AVAILABLE_MODELS.keys())
    else:
        models = list(AVAILABLE_MODELS.keys())

    # Select tests by profile
    tests = select_tests_profile(profile)
    print(f"[MODEL_BENCH] Profile: {profile}. Tests per model: {len(tests)}")
    print(f"[MODEL_BENCH] Models: {models}")

    bench = ModelBenchmark(results_dir=RESULTS_DIR, repeats=REPEATS)

    # --- Preflight: warn unresolved entities (action/status only) ---
    unresolved = []
    for t in tests:
        if t.get("category") in {"action", "status"}:
            eid = _resolve_entity(t["domain"], t["device"], bench.entity_map)
            if not eid:
                unresolved.append(f'{t["category"]}: {t["command"]}  ({t["domain"]}/{t["device"]})')
    if unresolved:
        print("[MODEL_BENCH][WARN] Unresolved entity_id for the following tests:")
        for line in unresolved[:20]:
            print("  -", line)
        if len(unresolved) > 20:
            print(f"  ... (+{len(unresolved)-20} more)")

    # Run
    ModelBenchmark(results_dir=RESULTS_DIR, repeats=REPEATS).run_tests(tests, models)
