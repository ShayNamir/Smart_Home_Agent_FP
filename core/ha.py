import requests
from typing import List, Dict, Any, Optional, Union, Sequence
from .objects import HAObject


ha_object = HAObject(url="http://localhost:8123", token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI5Yzc4YTNlODg4ODU0ZmEwYmRlMmIwNTA2NzI0ZmQ3NSIsImlhdCI6MTc1NzkzMzQyMSwiZXhwIjoyMDczMjkzNDIxfQ.LBAu_NNx9HuISTXLwd47IyqCrleBJpHG1xYXNH7JP7Q")
def get_entities_by_domain(domain: str = "") -> List[Dict[str, str]]:
    """
    Returns a list of entities in a compact format: [{"entity_id": "...", "name": "..."}].

    Behavior:
    - If domain is empty ("") → returns all entities from all domains (default, no change).
    - If domain is not empty → returns all entities of the requested domain + all entities of the 'switch' domain.
      (prevents duplicates; entities of the requested domain are arranged first, then switch entities.)
    """
    import requests
    from typing import List, Dict

    base = ha_object.url.rstrip("/")
    headers = {"Authorization": f"Bearer {ha_object.token}"}
    r = requests.get(f"{base}/api/states", headers=headers, timeout=8)
    r.raise_for_status()
    all_states = r.json()

    d = (domain or "").strip().lower().rstrip(".")
    # prefixes for entity selection
    if not d:
        wanted_prefixes = None         # all domains
    else:
        wanted_prefixes = {f"{d}.", "switch."}  # requested domain + switch

    results: List[Dict[str, str]] = []
    seen: set[str] = set()

    for s in all_states:
        eid = s.get("entity_id", "")
        if not eid:
            continue

        # filter by required domains (or all if None)
        if wanted_prefixes is not None and not any(eid.startswith(p) for p in wanted_prefixes):
            continue

        name = (s.get("attributes") or {}).get("friendly_name") or eid

        if eid not in seen:
            results.append({"entity_id": eid, "name": name})
            seen.add(eid)

    # sorting: first entities of requested domain, then switch, then by name
    if wanted_prefixes is not None:
        def sort_key(item: Dict[str, str]):
            eid = item["entity_id"]
            primary_rank = 0 if eid.startswith(f"{d}.") else (1 if eid.startswith("switch.") else 2)
            return (primary_rank, item["name"].casefold())
        results.sort(key=sort_key)
    else:
        results.sort(key=lambda x: x["name"].casefold())

    return results

def service_call(
    domain: str,
    service: str,
    entity_id: Optional[Union[str, List[str]]] = None,
    service_data: Optional[Dict[str, Any]] = None,
    target: Optional[Dict[str, Union[str, Sequence[str]]]] = None,
) -> Dict[str, Any]:
    """
    HA service call (supports multiple entities and area/device/entity target).
    entity_id: str | List[str] - single entity identifier or list of identifiers for multi-entity operation
    """
    base = ha_object.url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {ha_object.token}",
        "Content-Type": "application/json",
    }
    url = f"{base}/api/services/{domain}/{service}"

    payload: Dict[str, Any] = {}
    if target:
        # can leave as received; HA accepts string or list for each field
        payload["target"] = target
    if entity_id is not None:
        payload["entity_id"] = entity_id
    if service_data:
        payload.update(service_data)

    resp = requests.post(url, json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()

def list_services_for_domain(domain: str = "") -> List[Dict[str, Any]]: 
    """
    Returns a list of services for each domain (or for a specific domain if passed).
    Each item: {
      "domain": "light",
      "service": "turn_on",
      "description": "...",
      "fields": [{"name": "entity_id", "required": true/false/None, "description": "...", "example": "..."}],
      "tool_example": {"domain": "light", "service": "turn_on", "entity_id": "<entity_id?>", "service_data": {...}}
    }
    """
    base = ha_object.url.rstrip("/")
    headers = {"Authorization": f"Bearer {ha_object.token}"}
    r = requests.get(f"{base}/api/services", headers=headers, timeout=10)
    r.raise_for_status()
    services_doc = r.json()

    wanted = (domain or "").strip().lower()
    out: List[Dict[str, Any]] = []

    for d in services_doc:
        dom = d.get("domain", "")
        if wanted and dom != wanted:
            continue

        for svc_name, meta in (d.get("services") or {}).items():
            fields = []
            fields_meta = (meta.get("fields") or {})
            for fname, fmeta in fields_meta.items():
                fields.append({
                    "name": fname,
                    "required": fmeta.get("required"),
                    "description": fmeta.get("description"),
                    "example": fmeta.get("example"),
                })

            # build example that matches your service_call_tool
            entity_id_present = "entity_id" in fields_meta
            example_data = {k: ("" if k == "entity_id" else fields_meta[k].get("example", "")) for k in fields_meta.keys() if k != "entity_id"}

            tool_example = {
                "domain": dom,
                "service": svc_name,
                "entity_id": "<entity_id>" if entity_id_present else "",
                "service_data": example_data or None,
            }

            out.append({
                "domain": dom,
                "service": svc_name,
                "description": meta.get("description"),
                "fields": fields,
                "tool_example": tool_example,
            })

    return out


def get_entities_details(
    entity_ids: List[str],
    *,
    bulk_threshold: int = 15,
    timeout: float = 8.0,
) -> List[Dict[str, Any]]:
    """
    Takes a list of entity_id and returns full state details for each one, in the order provided.
    Removes duplicates, ignores entities that were not found.

    Optimization:
    - If number of requested entities >= bulk_threshold → single call to /api/states and local filtering.
    - Otherwise → individual requests to /api/states/{entity_id} (saves unnecessary traffic).
    - Uses requests.Session for connection/header reuse.

    Output for each entity:
    {
      "entity_id": "...",
      "name": "<friendly_name|entity_id>",
      "domain": "<prefix before the dot>",
      "state": "on|off|...",
      "attributes": {...},
      "last_changed": "...",
      "last_updated": "...",
      "context": {...}
    }
    """
    # input filtering/normalization: only non-empty strings, no duplicates, preserve order
    wanted = list(dict.fromkeys(e for e in entity_ids if isinstance(e, str) and e.strip()))
    if not wanted:
        return []

    base = ha_object.url.rstrip("/")
    token = ha_object.token

    results: List[Dict[str, Any]] = []

    def _pack(s: Dict[str, Any]) -> Dict[str, Any]:
        eid = s.get("entity_id", "")
        attrs = s.get("attributes") or {}
        return {
            "entity_id": eid,
            "name": attrs.get("friendly_name") or eid,
            "domain": (eid.split(".", 1)[0] if "." in eid else None),
            "state": s.get("state"),
            "attributes": attrs,
            "last_changed": s.get("last_changed"),
            "last_updated": s.get("last_updated"),
            "context": s.get("context"),
        }

    with requests.Session() as sess:
        sess.headers.update({"Authorization": f"Bearer {token}"})

        if len(wanted) >= bulk_threshold:
            # single request for all states then fast local filtering
            r = sess.get(f"{base}/api/states", timeout=timeout)
            r.raise_for_status()
            all_states = r.json()

            wanted_set = set(wanted)
            found: Dict[str, Dict[str, Any]] = {}
            for s in all_states:
                eid = s.get("entity_id")
                if eid in wanted_set:
                    found[eid] = _pack(s)

            # preserve input order, only what was found
            for eid in wanted:
                if eid in found:
                    results.append(found[eid])

        else:
            # individual calls (efficient when requesting few entities)
            for eid in wanted:
                try:
                    r = sess.get(f"{base}/api/states/{eid}", timeout=timeout)
                    if r.status_code == 200:
                        results.append(_pack(r.json()))
                except requests.RequestException:
                    # ignore individual errors; can log if needed
                    continue

    return results
