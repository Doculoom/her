from langchain_core.messages import AIMessage

from app.agents.her_agent import HerAgent
from app.agents.search_agent import SearchAgent
from app.agents.vault_agent import VaultAgent
from app.models.agent_models import HerState, HerResponse


def vault_node(state: HerState):
    res = VaultAgent().act(state)
    if not res:
        return state

    state["context"] = res.context

    if state["search_needed"]:
        state["next_node"] = "search"
    else:
        state["next_node"] = "end"
        if res.response:
            state["messages"].append(AIMessage(content=res.response, name="agent"))

    return state


def her_node(state: HerState):
    res: HerResponse = HerAgent().act(state)
    if not res:
        return state

    state["search_needed"] = res.search_needed
    state["search_query"] = res.search_query
    state["context"] = res.context

    if res.memories_needed:
        state["next_node"] = "vault"
    elif res.search_needed:
        state["next_node"] = "search"
    else:
        state["next_node"] = "end"
        if res.response:
            state["messages"].append(AIMessage(content=res.response, name="agent"))
    return state


def search_node(state: HerState):
    SearchAgent().act(state)
    return state
