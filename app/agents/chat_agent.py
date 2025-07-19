from langchain_core.prompts import PromptTemplate
from langchain.schema import AIMessage

from app.agents.base_agent import BaseAgent
from app.agents.vault_agent import VaultAgent
from app.core.prompt_templates import chat_agent_template
from app.models.agent_models import ChatResponse, ChatAgentState
from app.utils.helper import get_current_date_time_info
from app.memory.cortex import Cortex


cortex = Cortex()


class ChatAgent(BaseAgent):
    async def act(self, state: ChatAgentState) -> ChatAgentState:
        user_id = state.get("user_id")
        messages = state.get("messages")

        (
            curr_date,
            curr_day,
            curr_time,
        ) = get_current_date_time_info()

        memories = VaultAgent().retrieve_memories_text(user_id)
        prompt = PromptTemplate.from_template(chat_agent_template)
        p = prompt.invoke(
            {
                "current_day": curr_day,
                "current_time": curr_time,
                "current_date": curr_date,
                "memories": memories,
                "messages": messages,
            }
        )

        res = self.llm.with_structured_output(ChatResponse).invoke(p)
        state["initiate_chat"] = res.initiate_chat

        if res and res.initiate_chat and res.response is not None:
            state["response"] = res.response
            state["search_needed"] = res.search_needed
            state["search_query"] = res.search_query
            state["context"] = res.context
            state["next_node"] = "search"
        else:
            state["next_node"] = "end"

        return state


async def chat_node(state: ChatAgentState):
    res: ChatAgentState = await ChatAgent().act(state)
    if res["next_node"] == "end":
        return state

    state["search_needed"] = res["search_needed"]
    state["search_query"] = res["search_query"]
    state["context"] = res["context"]

    if res["search_needed"]:
        state["next_node"] = "search"
    else:
        state["next_node"] = "end"
        if res["response"]:
            state["messages"].append(AIMessage(content=res["response"], name="agent"))

    return state
