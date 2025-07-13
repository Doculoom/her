from functools import cache

from langchain.chat_models import init_chat_model
from vertexai.generative_models import Tool, grounding

from app.core.config import settings

search_tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())


@cache
def get_langchain_model(model_name: str = settings.MODEL):
    llm = init_chat_model(model_name)
    llm_with_search = llm.bind_tools([search_tool])
    return llm_with_search
