from langgraph.graph import StateGraph, END

from app.agents.agent_factory import her_node, vault_node, search_node
from app.models.agent_models import HerState

workflow = StateGraph(HerState)

workflow.add_node("her", her_node)
workflow.add_node("vault", vault_node)
workflow.add_node("search", search_node)

workflow.set_entry_point("her")

workflow.add_conditional_edges(
    "her",
    lambda s: s.get("next_node"),
    {"vault": "vault", "search": "search", "end": END},
)
workflow.add_conditional_edges(
    "vault",
    lambda s: s.get("next_node"),
    {"search": "search", "end": END},
)

workflow.add_edge("search", END)

converse = workflow.compile()
