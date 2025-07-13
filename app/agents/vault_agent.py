import logging
from collections import defaultdict
from typing import List
from urllib.parse import urlencode

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
        logging.info("Vault agent thinking..")
        conv = messages_to_string(state["user_name"], state["messages"])
        memories = self.retrieve_memories(state)
        current_date, current_day, current_time = get_current_date_time_info()

        prompt = PromptTemplate.from_template(vault_agent_template)
        p = prompt.invoke(
            {
                "messages": conv,
                "memories": memories,
                "current_day": current_day,
                "current_time": current_time,
                "current_date": current_date,
                "first_name": state["user_name"],
            }
        )

        res = self.llm.with_structured_output(HerResponse).invoke(p)
        print(f"Vault res: {res}")
        return res

    @staticmethod
    def retrieve_memories(state: HerState) -> str:
        print(
            f"Retrieving memories for {state['user_name']}; context: {state['context']}"
        )
        url = settings.VAULT_API_URL + "api/v1/memories/search"
        headers = {"Content-Type": "application/json"}
        payload = {
            "user_id": str(state["user_id"]),
            "text": state["context"],
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            memories_text = ""
            for memory_dict in data:
                memories_text += memory_dict["text"] + ", "
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
    def retrieve_all_memories(user_id: str = None, fields: str = None) -> List[str]:
        url = settings.VAULT_API_URL + "api/v1/memories"
        query_params = {}

        if user_id is not None:
            query_params["user_id"] = user_id
        if fields is not None:
            query_params["fields"] = fields
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise
        except requests.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            raise
        except ValueError as val_err:
            print(f"Value error: {val_err}")
            raise

    def retrieve_memories_text(self, user_id: str = None):
        fields = ["user_id", "text"]
        field_str = ", ".join(fields)
        data = self.retrieve_all_memories(user_id, field_str)
        memories = defaultdict(str)

        for item in data:
            memories[item["user_id"]] += item["text"] + " "

        res = []
        for memory in memories:
            dic = {"user_id": memory, "text": memories[memory]}
            res.append(dic)

        return str(res)

    def retrieve_memories_list(self, user_id: str = None):
        field_str = ", ".join(["id", "text"])
        data = self.retrieve_all_memories(user_id, field_str)
        memories = []

        for item in data:
            memory = {"memory_id": item["id"], "text": item["text"]}
            memories.append(memory)

        return str(memories)

    @staticmethod
    def create_memory(user_id: str, memory_text: str) -> Memory:
        url = settings.VAULT_API_URL + f"api/v1/memories?user_id={user_id}"
        headers = {"Content-Type": "application/json"}
        payload = MemoryCreateRequest(user_id=user_id, text=memory_text)
        response = requests.post(url, headers=headers, json=payload.dict())
        response.raise_for_status()
        data = response.json()
        return data

    @staticmethod
    def update_memory(user_id: str, memory_id: str, text: str) -> Memory:
        url = settings.VAULT_API_URL + f"api/v1/memories/{memory_id}?user_id={user_id}"
        headers = {"Content-Type": "application/json"}
        payload = MemoryUpdateRequest(user_id=user_id, text=text)
        response = requests.put(url, headers=headers, json=payload.dict())
        response.raise_for_status()
        data = response.json()
        return data
