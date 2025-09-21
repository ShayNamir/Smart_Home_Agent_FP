from __future__ import annotations
from typing import Any
import re
from agent_runner import AgentRunner, ModelType

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


_STANDARD_SUFFIX = """
Actions MUST include a service_call_tool call before replying.
Status MUST include a get_entities_details_tool call before replying.
Use tools only; never guess. Reply with ONE short English sentence.
""".strip()

def call_agent(user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
    # Temporarily disabled debug prints
    # print(f"CALLING STANDARD AGENT: Starting agent with prompt: {user_text}")
    runner = AgentRunner()
    model = runner.available_models[model_type]()
    ag = runner._load_standard_agent(model)
    prompt = f"{user_text}\n\n{_STANDARD_SUFFIX}"
    res = ag.run_sync(prompt)
    return _sanitize_output(_to_text(res))