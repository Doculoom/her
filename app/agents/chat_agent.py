from langchain_core.prompts import PromptTemplate

from app.agents.base_agent import BaseAgent
from app.agents.vault_agent import VaultAgent
from app.core.prompt_templates import chat_agent_template
from app.models.agent_models import ChatResponse
from app.services.message_handler import finish_sending_message
from app.utils.helper import get_current_date_time_info
from app.memory.cortex import Cortex


class ChatAgent(BaseAgent):
    async def act(self, user_name: str, user_id: str, chat_id: str):
        cortex = Cortex()

        (
            curr_date,
            curr_day,
            curr_time,
        ) = get_current_date_time_info()
        memories = VaultAgent().retrieve_memories_text(user_id)
        messages = cortex.get_messages(chat_id, 10)
        print(f"user_name: {user_name}, memories: {memories}")

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

        if res and res.initiate_chat and res.message is not None:
            print(f"Initiating conversation with {user_name}; Message: {res.message}")
            await finish_sending_message(
                chat_id, user_id, user_name, res.message, False
            )
