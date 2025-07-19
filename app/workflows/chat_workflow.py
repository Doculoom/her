from langgraph.graph import StateGraph, END

from app.agents.agent_factory import search_node
from app.agents.chat_agent import chat_node
from app.models.agent_models import ChatAgentState

workflow = StateGraph(ChatAgentState)

workflow.add_node("chat", chat_node)
workflow.add_node("search", search_node)

workflow.set_entry_point("chat")

workflow.add_conditional_edges(
    "chat",
    lambda s: s.get("next_node"),
    {"search": "search", "end": END},
)

workflow.add_edge("chat", END)
workflow.add_edge("search", END)

chat_workflow = workflow.compile()
