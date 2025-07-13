from functools import cache
from vertexai.generative_models import GenerativeModel, Tool, grounding
import vertexai
from app.core.config import settings
from app.utils.llm_helpers import build_prompt_with_output_instructions


class GroundedLLMWrapper:
    def __init__(self, model_name, with_grounding=True):
        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
        self.model = GenerativeModel(model_name)
        self.tools = []
        if with_grounding:
            self.tools.append(
                Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())
            )

    def invoke(self, prompt):
        return self.model.generate_content(prompt, tools=self.tools)

    def with_structured_output(self, pydantic_model):
        class StructuredOutputWrapper:
            def __init__(self, outer):
                self.outer = outer

            def invoke(self, prompt):
                prompt_with_instr = build_prompt_with_output_instructions(
                    prompt, pydantic_model
                )
                resp = self.outer.invoke(prompt_with_instr)
                try:
                    return pydantic_model.model_validate_json(resp.text)
                except Exception:
                    try:
                        return pydantic_model.model_validate(resp.text)
                    except Exception:
                        return pydantic_model(response=resp.text)

        return StructuredOutputWrapper(self)


@cache
def get_langchain_model(model_name: str = settings.MODEL):
    llm_with_search = GroundedLLMWrapper(model_name)
    return llm_with_search
