from langchain_core.prompts import PromptTemplate


from app.agents.base_agent import BaseAgent
from app.core.prompt_templates import her_agent_template
from app.models.agent_models import HerState, HerResponse
from app.utils.helper import get_current_date_time_info, messages_to_string


class HerAgent(BaseAgent):
    def act(self, state: HerState):
        conv = messages_to_string(state["user_name"], state["messages"])
        (
            curr_date,
            curr_day,
            curr_time,
        ) = get_current_date_time_info()

        prompt = PromptTemplate.from_template(her_agent_template)
        p = prompt.invoke(
            {
                "messages": conv,
                "current_day": curr_day,
                "current_time": curr_time,
                "current_date": curr_date,
                "first_name": state["user_name"],
            }
        )

        res = self.llm.with_structured_output(HerResponse).invoke(p)
        return res
