from langgraph.graph import StateGraph, END

from app.agents.agent_factory import her_node, vault_node
from app.models.agent_models import HerState

workflow = StateGraph(HerState)

workflow.add_node("her", her_node)
workflow.add_node("vault", vault_node)

workflow.set_entry_point("her")
workflow.add_conditional_edges(
    "her",
    lambda state: state.get("next_node"),
    {
        "vault": "vault",
        "end": END
    }
)
workflow.add_edge("vault", END)

converse = workflow.compile()
