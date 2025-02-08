from typing import Dict
from langchain_core.messages import AIMessage

from app.agents.base_agent import BaseAgent
from app.agents.chat_agent import ChatAgent
from app.agents.her_agent import HerAgent
from app.agents.summary_agent import SummaryAgent
from app.agents.vault_agent import VaultAgent
from app.models.agent_models import HerState, HerResponse

agent_registry: Dict[str, BaseAgent | VaultAgent | HerAgent | SummaryAgent] = {
    "her": HerAgent(),
    "vault": VaultAgent(),
    "summary": SummaryAgent(),
    "chat": ChatAgent(),
}


def vault_node(state: HerState):
    res = agent_registry.get("vault").act(state)
    state["messages"].append(AIMessage(content=res.response, name="agent"))
    return state


def her_node(state: HerState):
    res: HerResponse = agent_registry.get("her").act(state)

    if res.memories_needed:
        state["next_node"] = "vault"
        state["context"] = res.context
    else:
        state["next_node"] = "end"
        state["messages"].append(AIMessage(content=res.response, name="agent"))

    return state
