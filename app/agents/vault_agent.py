import requests

from langchain_core.prompts import PromptTemplate

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.core.prompt_templates import vault_agent_template
from app.models.agent_models import HerState, HerResponse
from app.models.memory_models import Memory, MemoryCreateRequest, MemoryUpdateRequest
from app.utils.helper import messages_to_string, get_current_date_time_info


class VaultAgent(BaseAgent):
    def act(self, state: HerState) -> HerResponse:
        conv = messages_to_string(state["user_name"], state["messages"])
        memories = self.retrieve_memories(state)
        current_date, current_day, current_time = get_current_date_time_info()

        prompt = PromptTemplate.from_template(vault_agent_template)
        p = prompt.invoke({
            "messages": conv,
            "user_channel": state["user_channel"],
            "memories": memories,
            "current_day": current_day,
            "current_time": current_time,
            "current_date": current_date,
            "first_name": state["user_name"],
        })

        res = self.llm.with_structured_output(HerResponse).invoke(p)
        return res

    @staticmethod
    def retrieve_memories(state: HerState) -> str:
        print(f"Retrieving memories for {state['user_name']}; context: {state['context']}")
        url = settings.VAULT_API_URL + 'api/v1/memories/search'
        headers = {'Content-Type': 'application/json'}
        payload = {
            'user_id': str(state['user_id']),
            'text': state['context'],
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            memories_text = ""
            for memory_dict in data:
                memories_text += memory_dict["text"] + ', '
            return memories_text[:-2] if memories_text else ""
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise
        except requests.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise
        except ValueError as val_err:
            print(f"Value error: {val_err}")
            raise

    @staticmethod
    def retrieve_all_memories(user_id) -> str:
        print(f"Retrieving all memories for {user_id}")
        url = settings.VAULT_API_URL + f'api/v1/memories/?user_id={user_id}'
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            memories_text = ''

            for i, m in enumerate(data):
                text = f"""
                memory:
                    memory_id: {m["id"]}
                    text: {m["text"]} \n
                """
                memories_text += text

            return memories_text
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise
        except requests.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise
        except ValueError as val_err:
            print(f"Value error: {val_err}")
            raise

    @staticmethod
    def create_memory(user_id: str, memory_text: str) -> Memory:
        url = settings.VAULT_API_URL + f'api/v1/memories?user_id={user_id}'
        headers = {'Content-Type': 'application/json'}
        payload = MemoryCreateRequest(user_id=user_id, text=memory_text)
        response = requests.post(url, headers=headers, json=payload.dict())
        response.raise_for_status()
        data = response.json()
        return data

    @staticmethod
    def update_memory(user_id: str, memory_id: str, text: str) -> Memory:
        url = settings.VAULT_API_URL + f'api/v1/memories/{memory_id}?user_id={user_id}'
        headers = {'Content-Type': 'application/json'}
        payload = MemoryUpdateRequest(user_id=user_id, text=text)
        response = requests.put(url, headers=headers, json=payload.dict())
        response.raise_for_status()
        data = response.json()
        return data



