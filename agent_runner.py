# agent_runner.py
from __future__ import annotations
from typing import Callable, Dict, List, Any, Optional, Union
from enum import Enum
import importlib

from pydantic_ai import Agent
from pydantic_ai.models import ModelSettings
from pydantic_ai.models.openai import OpenAIModel
# OpenAIProvider not required in this version

# Replace with your path if different
from core.ha import (
    get_entities_by_domain,
    get_entities_details,
    list_services_for_domain,
    service_call,
)

DEFAULT_SYSTEM_PROMPT = (
"""
You are a small, fast Home Assistant agent. Use tools only; never guess names/services/entity_id.
Tools: get_entities_by_domain_tool, get_entities_details_tool, service_call_tool.

ACTION flow:
1) get_entities_by_domain_tool(domain)
2) service_call_tool(domain, service, entity_id, data or {})
→ then return ONE short, friendly sentence.

STATUS flow:
1) get_entities_by_domain_tool(domain)
2) get_entities_details_tool([entity_id])
→ then return ONE short, friendly sentence.

Final reply: no JSON, no tool names, no reasoning.
Service hints: light/switch/fan → turn_on/turn_off; lock → lock/unlock.
EXAMPLE:
# Action
User: Turn on the bed light.
Call: get_entities_by_domain_tool("light") → ["light.bed_light", …]
Call: service_call_tool("light","turn_on","light.bed_light",{})
Final reply: Bed light turned on.

# Status
User: Is the bed light on?
Call: get_entities_by_domain_tool("light") → ["light.bed_light", …]
Call: get_entities_details_tool(["light.bed_light"]) → state="on"
Final reply: Bed light is on.
"""
)

class ModelType(Enum):
    OLLAMA_QWEN3_4B      = "ollama_qwen3_4b"
    OLLAMA_GEMMA3_4B     = "ollama_gemma3_4b"
    OLLAMA_LLAMA3_2      = "ollama_llama3_2_latest"
    OLLAMA_MISTRAL       = "ollama_mistral_latest"
    OLLAMA_PHI3_MINI     = "ollama_phi3_mini"
    OLLAMA_DEEPSEEK_R1   = "ollama_deepseek_r1_1_5b"

class AgentRunner:
    """
    Bridge for creating agents, registering models, loading tools, and running architectures.
    """
    def __init__(
        self,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        temperature: float = 0.2,
        request_timeout: Optional[int] = None,           # seconds; applied via ModelSettings if supported
        ollama_base_url: str = "http://localhost:11434/v1",
        ollama_api_key: str = "ollama",                  # dummy value works for Ollama
    ) -> None:
        self.system_prompt = system_prompt
        self.temperature = float(temperature)
        self.request_timeout = request_timeout
        self.ollama_base_url = ollama_base_url
        self.ollama_api_key = ollama_api_key

        # Register factories for each available model
        self.available_models: Dict[ModelType, Callable[[], Any]] = {
            ModelType.OLLAMA_QWEN3_4B:    self._ollama_factory("qwen3:4b"),
            ModelType.OLLAMA_GEMMA3_4B:   self._ollama_factory("gemma3:4b"),
            ModelType.OLLAMA_LLAMA3_2:    self._ollama_factory("llama3.2:latest"),
            ModelType.OLLAMA_MISTRAL:     self._ollama_factory("mistral:latest"),
            ModelType.OLLAMA_PHI3_MINI:   self._ollama_factory("phi3:mini"),
            ModelType.OLLAMA_DEEPSEEK_R1: self._ollama_factory("deepseek-r1:1.5b"),
        }

    # -------- Model factories --------
    def _ollama_factory(self, model_name: str) -> Callable[[], Any]:
        def _build() -> Any:
            return OpenAIModel(
                model_name,
                base_url=self.ollama_base_url,
                api_key=self.ollama_api_key
            )
        return _build

    # -------- Agent builders --------
    def _register_tools(self, agent: Agent) -> None:
        @agent.tool_plain
        def get_entities_by_domain_tool(domain: str = "") -> List[dict]:
            """
            This tool is used to get a list of entities by domain.
            """
            # Temporarily disabled debug prints
            # print(f"get_entities_by_domain_tool: {domain}")
            ans= get_entities_by_domain(domain)
            # print(f"Number of entities: {len(ans)}")
            return ans

        @agent.tool_plain
        def get_entities_details_tool(entity_ids: List[str]) -> List[dict]:
            """
            This tool is used to get the details and current state of an entity.
            """
            # Temporarily disabled debug prints
            # print(f"get_entities_details_tool: {entity_ids}")
            return get_entities_details(entity_ids)

        #@agent.tool_plain
        #def list_domain_services_tool(domain: str) -> List[dict]:
        #    """
        #    This tool is used to get a list of available services by domain.
        #    """
        #    print(f"list_domain_services_tool: {domain}")
        #    return list_services_for_domain(domain)

        @agent.tool_plain
        def service_call_tool(
            domain: str,
            service: str,
            entity_id: Union[str, List[str]],
            service_data: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """
            This tool is used to call a service on an entity. for perdorming an action.
            """
            # Temporarily disabled debug prints
            # print(f"service_call_tool: {domain}, {service}")
            return service_call(domain, service, entity_id, service_data)

    def _build_agent(self, model: Any, system_prompt: Optional[str] = None) -> Agent:
        agent = Agent(
            model=model,
            system_prompt=(system_prompt or self.system_prompt),
            model_settings=ModelSettings(
                temperature=self.temperature,
                timeout=(self.request_timeout if self.request_timeout is not None else None),
            ),
        )
        self._register_tools(agent)
        return agent

    # Architectures that build the same Agent — differences are in prompts in Arch.* modules
    def _load_standard_agent(self, model: Any) -> Agent:
        return self._build_agent(model)

    def _load_cot_agent(self, model: Any) -> Agent:
        return self._build_agent(model)

    def _load_react_agent(self, model: Any) -> Agent:
        return self._build_agent(model)

    def _load_reflexion_agent(self, model: Any) -> Agent:
        return self._build_agent(model)

    def _load_tot_agent(self, model: Any) -> Agent:
        return self._build_agent(model)

    # -------- Architecture dispatch --------
    _ARCH_MODULES: Dict[str, str] = {
        "standard":   "Arch.standard",
        "cot":        "Arch.cot",
        "react":      "Arch.react",
        "reflexion":  "Arch.reflexion",
        "self_refine":"Arch.reflexion",
        "tot":        "Arch.tot",
        # "debate":   "Arch.debate",          # if you add
        # "sc":       "Arch.self_consistency", # if you add
    }

    def run(self, architecture: str, user_text: str, model_type: ModelType, timeout_s: int = 120) -> str:
        arch = architecture.lower()
        if arch not in self._ARCH_MODULES:
            raise ValueError(f"Unknown architecture: {architecture}")

        module_path = self._ARCH_MODULES[arch]
        mod = importlib.import_module(module_path)
        if not hasattr(mod, "call_agent"):
            raise RuntimeError(f"Architecture module '{module_path}' missing 'call_agent'")

        return mod.call_agent(user_text, model_type, timeout_s)