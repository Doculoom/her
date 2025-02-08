from app.core.prompt_templates import base_agent_template
from app.utils.helper import get_current_date_time_info


class PromptGenerator:
    @staticmethod
    def generate_system_prompt(user_details={}):
        current_date, current_day, current_time = get_current_date_time_info()

        formatting_data = {
            "current_day": current_day,
            "current_time": current_time,
            "current_date": current_date,
            **user_details,
        }

        system_prompt = base_agent_template.format(**formatting_data)
        return system_prompt

    @staticmethod
    def generate_prompt(description, details={}):
        prompt = description.format(**details)
        return prompt
