from langchain_core.prompts import PromptTemplate

from app.agents.base_agent import BaseAgent
from app.core.prompt_templates import summary_agent_template, summary_merge_agent_template
from app.models.memory_models import GeneratedMemoryList, UpdatedMemoryList

from app.utils.helper import get_current_date_time_info, messages_to_string


class SummaryAgent(BaseAgent):
    def generate_memory(self, user_name, messages) -> GeneratedMemoryList:
        curr_date, curr_day, curr_time,  = get_current_date_time_info()
        conv = messages_to_string(user_name, messages)
        prompt = PromptTemplate.from_template(summary_agent_template)
        p = prompt.invoke({
            "messages": conv, "current_day": curr_day, "current_date": curr_date,
            "first_name": user_name, "current_time": curr_time
        })
        res = self.llm.with_structured_output(GeneratedMemoryList).invoke(p)
        return res

    def update_memories(self, old_memories: str, new_memories: str) -> UpdatedMemoryList:
        prompt = PromptTemplate.from_template(summary_merge_agent_template)
        p = prompt.invoke({
            "old_memories": old_memories, "new_memories": new_memories
        })
        res = self.llm.with_structured_output(UpdatedMemoryList).invoke(p)
        return res
