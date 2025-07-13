from functools import cache
from typing import TypeAlias

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

ModelT: TypeAlias = ChatGoogleGenerativeAI


@cache
def get_langchain_model(model_name: str = settings.MODEL) -> ModelT:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        tools=["google_search_retrieval"],
    )
    return llm
