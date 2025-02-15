from langchain_core.messages import AIMessage

from app.agents.her_agent import HerAgent
from app.agents.vault_agent import VaultAgent
from app.models.agent_models import HerState, HerResponse


def vault_node(state: HerState):
    res = VaultAgent().act(state)
    if not res:
        return state

    if res.response:
        state["messages"].append(AIMessage(content=res.response, name="agent"))
    return state


def her_node(state: HerState):
    res: HerResponse = HerAgent().act(state)
    if not res:
        return state

    if res.memories_needed:
        state["next_node"] = "vault"
        state["context"] = res.context
    else:
        state["next_node"] = "end"
        state["messages"].append(AIMessage(content=res.response, name="agent"))

    return state
