"""
benchmark_commands.py — Expanded benchmark command set for Smart Home Agent

Goal:
- Provide a LARGE yet controlled set of natural-language commands to test agent architectures.
- Devices remain EXACTLY as defined here (no additions/removals), but phrasing variety is high.
- Each test item includes: category, domain, device (friendly name), command, and (for actions) the intended action.

Usage (example):
    from benchmark_commands import BENCHMARK_TESTS
    for t in BENCHMARK_TESTS:
        # Temporarily disabled debug prints
        # print(t["category"], t["domain"], t["device"], "=>", t["command"])
"""

from __future__ import annotations
from typing import Dict, List, Literal

Category = Literal["action", "status", "error"]

# ---------------------------
# Devices (DO NOT CHANGE LISTS)
# ---------------------------
DEVICES: Dict[str, List[str]] = {
    "light": [
        "Bed Light",
        "Ceiling Lights",
        "Kitchen Lights",
        "Office Lights",
        "Living Room Lights",
        "Entrance Lights",
    ],
    "switch": [
        "Decorative Lights",
    ],
    "lock": [
        "Front Door",
        "Kitchen Door",
        "Openable Lock",
    ],
    "fan": [
        "Living Room Fan",
        "Ceiling Fan",
        "Percentage Full Fan",
        "Percentage Limited Fan",
        "Preset Only Limited Fan",
    ],
}

# ---------------------------
# Phrasing libraries
# ---------------------------
TURN_ON_SYNS = [
    "turn on the {d}",
    "switch on the {d}",
    "power on the {d}",
    "please turn on the {d}",
    "can you turn on the {d}",
    "enable the {d}",
    "activate the {d}",
]

TURN_OFF_SYNS = [
    "turn off the {d}",
    "switch off the {d}",
    "power off the {d}",
    "please turn off the {d}",
    "can you turn off the {d}",
    "disable the {d}",
    "deactivate the {d}",
]

LOCK_SYNS = [
    "lock the {d}",
    "please lock the {d}",
    "secure the {d}",
    "engage the lock on the {d}",
]

UNLOCK_SYNS = [
    "unlock the {d}",
    "please unlock the {d}",
    "open the {d}",
    "unsecure the {d}",
]

FAN_ON_SYNS = TURN_ON_SYNS  # same semantics
FAN_OFF_SYNS = TURN_OFF_SYNS
FAN_START_SYNS = [
    "start the {d}",
    "spin up the {d}",
    "run the {d}",
]
FAN_STOP_SYNS = [
    "stop the {d}",
    "halt the {d}",
    "stop running the {d}",
]

STATUS_SYNS_GENERIC = [
    "what is the state of the {d}",
    "what's the status of the {d}",
    "is the {d} on",
    "is the {d} off",
    "check the {d} status",
    "tell me the current state of the {d}",
]

STATUS_SYNS_LOCK = [
    "is the {d} locked",
    "is the {d} unlocked",
    "what is the status of the {d}",
    "check if the {d} is secure",
]

# ---------------------------
# Helper to normalize device mention inside phrasing
# ---------------------------
def dev_phrase(name: str) -> str:
    """Insert device name in lower case for more natural phrasing."""
    return name.lower()

# ---------------------------
# Build tests
# Each test is a dict:
# { "category": "action|status|error", "domain": str, "device": str, "command": str, "action": "turn_on|turn_off|lock|unlock|status|none" }
# ---------------------------
BENCHMARK_TESTS: List[Dict[str, str]] = []

def add_action(domain: str, device: str, templates: List[str], action: str) -> None:
    for t in templates:
        BENCHMARK_TESTS.append({
            "category": "action",
            "domain": domain,
            "device": device,
            "command": t.format(d=dev_phrase(device)),
            "action": action,
        })

def add_status(domain: str, device: str, templates: List[str]) -> None:
    for t in templates:
        BENCHMARK_TESTS.append({
            "category": "status",
            "domain": domain,
            "device": device,
            "command": (t + "?").replace("??", "?").format(d=dev_phrase(device)),
            "action": "status",
        })

# -------- Lights --------
for light in DEVICES["light"]:
    add_action("light", light, TURN_ON_SYNS, "turn_on")
    add_action("light", light, TURN_OFF_SYNS, "turn_off")
    add_status("light", light, STATUS_SYNS_GENERIC)

# -------- Switches --------
for sw in DEVICES["switch"]:
    add_action("switch", sw, TURN_ON_SYNS, "turn_on")
    add_action("switch", sw, TURN_OFF_SYNS, "turn_off")
    add_status("switch", sw, STATUS_SYNS_GENERIC)

# -------- Locks --------
for lk in DEVICES["lock"]:
    add_action("lock", lk, LOCK_SYNS, "lock")
    add_action("lock", lk, UNLOCK_SYNS, "unlock")
    add_status("lock", lk, STATUS_SYNS_LOCK)

# -------- Fans --------
for fan in DEVICES["fan"]:
    add_action("fan", fan, FAN_ON_SYNS + FAN_START_SYNS, "turn_on")
    add_action("fan", fan, FAN_OFF_SYNS + FAN_STOP_SYNS, "turn_off")
    add_status("fan", fan, STATUS_SYNS_GENERIC)

# ---------------------------
# Error / robustness tests (non-existent devices or malformed)
# ---------------------------
ERROR_COMMANDS = [
    # lights that don't exist
    "turn on the garden light",
    "switch off the hallway lamp",
    "activate the balcony lights",
    "please power on the garage light",
    # locks that don't exist
    "unlock the back gate",
    "lock the safe room door",
    # fans that don't exist
    "turn on the bathroom fan",
    "stop the attic fan",
    # malformed / vague
    "turn it on",
    "turn it off",
    "switch that one on",
    "please activate",
    "do the thing",
]

for cmd in ERROR_COMMANDS:
    BENCHMARK_TESTS.append({
        "category": "error",
        "domain": "unknown",
        "device": "unknown",
        "command": cmd,
        "action": "none",
    })

# ---------------------------
# Convenience groupings (optional)
# ---------------------------
def by_category(cat: Category) -> List[Dict[str, str]]:
    return [t for t in BENCHMARK_TESTS if t["category"] == cat]

def by_domain(domain: str) -> List[Dict[str, str]]:
    return [t for t in BENCHMARK_TESTS if t["domain"] == domain]

# Quick sanity if run directly
# Quick sanity if run directly
if __name__ == "__main__":
    import collections

    print(f"Total tests: {len(BENCHMARK_TESTS)}")
    cnt = collections.Counter(t["category"] for t in BENCHMARK_TESTS)
    print("By category:", dict(cnt))

    for cat in ["action", "status", "error"]:
        subset = by_category(cat)
        print(f"\n== {cat.upper()} ({len(subset)}) ==")
        for row in subset[:10]:
            print("-", row["command"])
        if len(subset) > 10:
            print(f"... (+{len(subset)-10} more)")

# ---------- Manual entity mapping (from user's HA) ----------
# Build a static mapping: domain -> { friendly_name : entity_id }
# Use exactly the lists you provided.

def build_entity_map():
    mapping = {
        "light": {
            "Bed Light": "light.bed_light",
            "Ceiling Lights": "light.ceiling_lights",
            "Entrance Color + White Lights": "light.entrance_color_white_lights",
            "Kitchen Lights": "light.kitchen_lights",
            "Living Room RGBWW Lights": "light.living_room_rgbww_lights",
            "Office RGBW Lights": "light.office_rgbw_lights",
        },
        "switch": {
            "Decorative Lights": "switch.decorative_lights",
        },
        "lock": {
            "Front Door": "lock.front_door",
            "Kitchen Door": "lock.kitchen_door",
            "Openable Lock": "lock.openable_lock",
            "Poorly Installed Door": "lock.poorly_installed_door",
        },
        "fan": {
            "Ceiling Fan": "fan.ceiling_fan",
            "Living Room Fan": "fan.living_room_fan",
            "Percentage Full Fan": "fan.percentage_full_fan",
            "Percentage Limited Fan": "fan.percentage_limited_fan",
            "Preset Only Limited Fan": "fan.preset_only_limited_fan",
        },
    }
    return mapping
