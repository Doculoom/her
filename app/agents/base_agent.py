from datetime import datetime

from app.core.llm import get_langchain_model


class BaseAgent:
    def __init__(self):
        self.llm = get_langchain_model()

    def act(self, state):
        raise NotImplementedError
