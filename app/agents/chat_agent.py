from langchain_core.prompts import PromptTemplate

from app.agents.base_agent import BaseAgent
from app.core.prompt_templates import chat_agent_template
from app.models.agent_models import ChatResponse
from app.utils.helper import get_current_date_time_info


class ChatAgent(BaseAgent):
    def act(self, user_name: str, user_id: str, channel_id: str):
        from app.memory.cortex import Cortex
        from app.agents.agent_factory import agent_registry
        from app.services.message_handler import add_message_to_queue

        cortex = Cortex()

        curr_date, curr_day, curr_time, = get_current_date_time_info()
        memories = agent_registry.get("vault").retrieve_memories_text(user_id, fields=["user_id", "text"])
        messages = cortex.get_messages(channel_id, 10)

        prompt = PromptTemplate.from_template(chat_agent_template)
        p = prompt.invoke({
            "current_day": curr_day,
            "current_time": curr_time,
            "current_date": curr_date,
            "memories": memories,
            "messages": messages,
        })

        res = self.llm.with_structured_output(ChatResponse).invoke(p)

        if res.message is not None:
            add_message_to_queue(user_id, "telegram", channel_id, res.message)
            cortex.add_agent_message(user_id, user_name, res.message)
