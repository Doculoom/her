import datetime

from app.core.prompt_templates import SYSTEM_TEMPLATE


class PromptGenerator:
    @staticmethod
    def generate_system_prompt(user_details={}):
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_day = now.strftime("%Y-%m-%d")

        formatting_data = {
            "current_time": current_time,
            "current_day": current_day,
            **user_details,
        }

        system_prompt = SYSTEM_TEMPLATE.format(**formatting_data)
        return system_prompt

    @staticmethod
    def generate_prompt(description, details={}):
        prompt = description.format(**details)
        return prompt




