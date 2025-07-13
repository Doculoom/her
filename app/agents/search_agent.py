import logging

from google import genai
from google.genai import types
from langchain.schema import AIMessage

from app.core.config import settings
from app.models.agent_models import HerState


class SearchAgent:
    def __init__(self, model_name: str = settings.MODEL):
        self.client = genai.Client()
        self.model_id = model_name
        self.config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_modalities=["TEXT"],
            max_output_tokens=1024,
        )

    @staticmethod
    def _friend_prompt(
        user_name: str,
        context: str,
        search_query: str,
        last_user_msg: str,
    ) -> str:
        head = (
            f"You are chatting with {user_name} as a helpful friend. "
            "Reply in a natural, friendly tone (1 – 3 short sentences). "
            "Blend any facts you retrieve into the reply and do NOT mention you used a search tool."
        )
        return (
            f"{head}\n\n"
            f'Latest user message:\n"{last_user_msg}"\n\n'
            "Context and search guidance from the previous agent:\n"
            f"{context}\n\n"
            "Search query:\n"
            f"{search_query}\n\n"
            "Reply to the user now."
        )

    def act(self, state: HerState):
        logging.info("Search agent thinking..")
        user_name = state["user_name"]
        search_query = state.get("search_query") or state["messages"][-1].content
        context = state.get("context")
        last_msg = state["messages"][-1].content

        prompt = self._friend_prompt(
            user_name=user_name,
            search_query=search_query,
            context=context,
            last_user_msg=last_msg,
        )

        resp = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=self.config,
        )
        answer = resp.candidates[0].content.parts[0].text

        state["messages"].append(AIMessage(content=answer, name="agent"))
        state["next_node"] = "end"
        return state
