from functools import lru_cache
import logging
from typing import Any, Optional

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

from app.core.config import settings
from app.utils.llm_helpers import build_prompt_with_output_instructions

logger = logging.getLogger(__name__)


class GroundedLLMWrapper:
    def __init__(self, model_name: str):
        self.client = genai.Client()
        self.model_id = model_name
        self.config = GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
            response_modalities=["TEXT"],
        )

    def invoke(self, prompt: str) -> Any:
        try:
            return self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=self.config,
            )
        except Exception as e:
            logger.error(f"invoke error: {e}")
            raise

    def with_structured_output(self, pydantic_model):
        class StructuredOutputWrapper:
            def __init__(self, outer: "GroundedLLMWrapper"):
                self.outer = outer

            @staticmethod
            def _extract_json(text: str) -> Optional[str]:
                try:
                    start, end = text.index("{"), text.rindex("}") + 1
                    return text[start:end]
                except ValueError:
                    return None

            def invoke(self, prompt: str) -> Any:
                prompt_with_instr = build_prompt_with_output_instructions(
                    prompt, pydantic_model
                )
                resp = self.outer.invoke(prompt_with_instr)
                response_text = resp.candidates[0].content.parts[0].text

                try:
                    return pydantic_model.model_validate_json(response_text)
                except Exception:
                    pass
                try:
                    return pydantic_model.model_validate(response_text)
                except Exception:
                    pass
                json_str = self._extract_json(response_text)
                if json_str:
                    try:
                        return pydantic_model.model_validate_json(json_str)
                    except Exception:
                        pass
                raise ValueError(
                    f"cannot parse response into {pydantic_model.__name__}: {response_text}"
                )

        return StructuredOutputWrapper(self)


@lru_cache(maxsize=128)
def get_langchain_model(model_name: str = settings.MODEL) -> GroundedLLMWrapper:
    return GroundedLLMWrapper(model_name)
