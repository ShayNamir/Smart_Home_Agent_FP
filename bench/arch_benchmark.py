# arch_bench/arch_benchmark.py — Architecture benchmark runner (CORE profile) for qwen3:4b (Ollama)
from __future__ import annotations

# ---- Global config tweaks ----
SKIP_ERROR = True  # exclude error tests

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
    # when running as module: python -m arch_bench.arch_benchmark
    from .benchmark_commands import BENCHMARK_TESTS, build_entity_map
except ImportError:
    # when running this file directly
    from benchmark_commands import BENCHMARK_TESTS, build_entity_map

# -------------------------
# Paths & constants
# -------------------------
RESULTS_DIR = "/Users/shaynamir/Library/CloudStorage/OneDrive-ArielUniversity/לימודים/קורסים/פרויקט גמר/Smart_Home_Agent_FP/bench/bench_results"
MODEL = ModelType.OLLAMA_QWEN3_4B

# Profile CORE: only these 3 architectures (≈180 tests)
ARCHITECTURES_CORE = ["react", "reflexion", "tot"]
ARCHITECTURES_ALL  = ["standard", "cot", "react", "reflexion", "tot"]

REPEATS = 1
CHECKPOINT_CSV = os.path.join(RESULTS_DIR, "bench_live.csv")

# Timing guards for HA state stabilization (keep short to speed up)
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

def _timestamped_filename(prefix: str = "bench") -> str:
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
      - 'core'  : ~60 tests (15 per domain x 4 domains) ⇒ 180 for 3 architectures.
      - 'lite'  : ~36 tests (9 per domain x 4 domains).
      - 'micro' : ~18 tests (≈4-5 per domain).
      - 'long'  : all non-error tests.
    """
    profile = (profile or "").strip().lower() or PROFILE_DEFAULT
    include_cats = {"action", "status"} if SKIP_ERROR else {"action", "status", "error"}
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
# Benchmark Runner
# -------------------------
class ArchitectureBenchmark:
    COLUMNS = [
        "architecture",
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
    def _run_action_test(self, arch: str, test: Dict[str, str]) -> Dict[str, str]:
        domain = test["domain"]
        device = test["device"]
        cmd    = test["command"]
        action = test.get("action", "")
        exp_init, exp_fin = _expected_states_for_action(action)

        entity_id = _resolve_entity(domain, device, self.entity_map)
        if not entity_id:
            start = time.perf_counter()
            resp = self.runner.run(arch, cmd, MODEL)
            dur  = time.perf_counter() - start
            return {
                "architecture": arch,
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
        resp = self.runner.run(arch, cmd, MODEL)
        dur  = time.perf_counter() - start

        if POST_ACTION_WAIT > 0: time.sleep(POST_ACTION_WAIT)
        act_fin = _safe_state(entity_id)

        return {
            "architecture": arch,
            "command": cmd,
            "category": "action",
            "response": resp,
            "run time": f"{dur:.2f}",
            "exp init state": exp_init,
            "exp fin state": exp_fin,
            "act init state": act_init,
            "act fin state": act_fin,
        }

    def _run_status_test(self, arch: str, test: Dict[str, str]) -> Dict[str, str]:
        domain = test["domain"]
        device = test["device"]
        cmd    = test["command"]

        entity_id = _resolve_entity(domain, device, self.entity_map)
        act_init = _safe_state(entity_id) if entity_id else "not_found"

        start = time.perf_counter()
        resp = self.runner.run(arch, cmd, MODEL)
        dur  = time.perf_counter() - start

        act_fin = _safe_state(entity_id) if entity_id else "not_found"

        return {
            "architecture": arch,
            "command": cmd,
            "category": "status",
            "response": resp,
            "run time": f"{dur:.2f}",
            "exp init state": "n/a",
            "exp fin state": "n/a",
            "act init state": act_init,
            "act fin state": act_fin,
        }

    def _run_error_test(self, arch: str, test: Dict[str, str]) -> Dict[str, str]:
        # Not expected under SKIP_ERROR=True, but kept for completeness
        cmd = test["command"]
        buf = io.StringIO()
        start = time.perf_counter()
        with redirect_stdout(buf):
            resp = self.runner.run(arch, cmd, MODEL)
        dur = time.perf_counter() - start
        logs = buf.getvalue().lower()
        called = "service_call_tool:" in logs
        return {
            "architecture": arch,
            "command": cmd,
            "category": "error",
            "response": resp,
            "run time": f"{dur:.2f}",
            "exp init state": "no_action",
            "exp fin state": "no_action",
            "act init state": "not_called",
            "act fin state": "called" if called else "not_called",
        }

    def _run_single(self, arch: str, test: Dict[str, str]) -> Dict[str, str]:
        cat = test["category"]
        if cat == "action":
            return self._run_action_test(arch, test)
        if cat == "status":
            return self._run_status_test(arch, test)
        return self._run_error_test(arch, test)

    def _load_done_keys(self) -> set:
        done_keys = set()
        if os.path.exists(CHECKPOINT_CSV):
            try:
                with open(CHECKPOINT_CSV, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        done_keys.add((r.get("architecture",""), r.get("command",""), r.get("category","")))
            except csv.Error:
                # fallback via pandas (no field-size limit)
                df = pd.read_csv(CHECKPOINT_CSV, engine="python")
                for _, r in df.iterrows():
                    done_keys.add((str(r.get("architecture","")), str(r.get("command","")), str(r.get("category",""))))
        return done_keys

    def run_tests(self, tests: List[Dict[str, str]], architectures: List[str]) -> str:
        rows: List[Dict[str, str]] = []

        done_keys = self._load_done_keys()
        print(f"[BENCH] Resuming: found {len(done_keys)} completed rows in checkpoint.")

        # compute total remaining for progress display
        remaining = []
        for arch in architectures:
            for test in tests:
                key = (arch, test.get("command",""), test.get("category",""))
                for _ in range(self.repeats):
                    if key not in done_keys:
                        remaining.append(key)
        total_remaining = len(remaining)
        idx = 0

        for arch in architectures:
            print(f"[BENCH] Running architecture: {arch} ({len(tests)} tests x {self.repeats} repeats)")
            for test in tests:
                cmd = test.get("command", "")
                cat = test.get("category", "")
                key = (arch, cmd, cat)

                for _ in range(self.repeats):
                    if key in done_keys:
                        continue

                    idx += 1
                    print(f"Test {idx}/{total_remaining} {arch}: {cmd}")
                    try:
                        row = self._run_single(arch, test)
                    except Exception as e:
                        row = {
                            "architecture": arch,
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

        # === Save a SINGLE Excel including ALL historical rows + current run ===
        filename = _timestamped_filename(prefix="bench")
        out_path = os.path.join(self.results_dir, filename)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        # Load all historical rows from checkpoint (combined) + new rows (this run)
        try:
            df_all = pd.read_csv(CHECKPOINT_CSV, engine="python")
        except Exception:
            df_all = pd.DataFrame(columns=self.COLUMNS)

        df_new = pd.DataFrame(rows, columns=self.COLUMNS)

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            # Sheet 1: ALL results (historical + current)
            df_all.to_excel(writer, index=False, sheet_name="results_all")
            # Sheet 2: only rows created in THIS run (for quick analysis)
            df_new.to_excel(writer, index=False, sheet_name="results_new")

            # Sheet 3: summary by architecture/category (ALL)
            if not df_all.empty and "run time" in df_all.columns:
                tmp = df_all.copy()
                tmp["run time"] = pd.to_numeric(tmp["run time"], errors="coerce")
                agg = (tmp.groupby(["architecture","category"])["run time"]
                         .agg(["count","mean","median","min","max"])
                         .reset_index())
                agg.to_excel(writer, index=False, sheet_name="summary_all")

        print(f"[BENCH] Saved results to: {out_path}")
        return out_path

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Profile choice (default core). Press Enter to accept CORE quickly.
    choice = input("Profile? [core|lite|micro|long] (default core): ").strip().lower()
    profile = choice or PROFILE_DEFAULT

    # Architectures: for CORE we default to react/reflexion/tot to reach ~180 tests total
    arch_choice = input("Architectures? [core|all|custom csv] (default core=react,reflexion,tot): ").strip().lower()
    if arch_choice == "all":
        architectures = ARCHITECTURES_ALL
    elif arch_choice.startswith("custom"):
        # e.g., "custom standard,cot"
        parts = arch_choice.replace("custom","").strip().strip(":, ")
        architectures = [a.strip() for a in parts.split(",") if a.strip()]
        if not architectures:
            architectures = ARCHITECTURES_CORE
    else:
        architectures = ARCHITECTURES_CORE

    # Select tests by profile
    tests = select_tests_profile(profile)
    if SKIP_ERROR:
        tests = [t for t in tests if (t.get("category","").lower() != "error")]
    print(f"[BENCH] Profile: {profile}. Tests per architecture: {len(tests)}")
    print(f"[BENCH] Architectures: {architectures}")

    bench = ArchitectureBenchmark(results_dir=RESULTS_DIR, repeats=REPEATS)

    # --- Preflight: warn unresolved entities (action/status only) ---
    unresolved = []
    for t in tests:
        if t.get("category") in {"action", "status"}:
            eid = _resolve_entity(t["domain"], t["device"], bench.entity_map)
            if not eid:
                unresolved.append(f'{t["category"]}: {t["command"]}  ({t["domain"]}/{t["device"]})')
    if unresolved:
        print("[BENCH][WARN] Unresolved entity_id for the following tests:")
        for line in unresolved[:20]:
            print("  -", line)
        if len(unresolved) > 20:
            print(f"  ... (+{len(unresolved)-20} more)")

    # Run
    ArchitectureBenchmark(results_dir=RESULTS_DIR, repeats=REPEATS).run_tests(tests, architectures)