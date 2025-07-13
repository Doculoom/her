from functools import lru_cache
from vertexai.generative_models import GenerativeModel, Tool
import vertexai
from app.core.config import settings
from app.utils.llm_helpers import build_prompt_with_output_instructions
import json
import logging
import re  # Moved import to top for consistency
from typing import Any, Optional

logger = logging.getLogger(__name__)


class GroundedLLMWrapper:
    def __init__(self, model_name: str, with_grounding: bool = True):
        vertexai.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_LOCATION)
        self.model = GenerativeModel(model_name)
        self.tools: list[Tool] = []
        if with_grounding:
            # Use google_search for Gemini 2.5 Pro compatibility
            self.tools.append(
                Tool.from_dict(
                    {
                        "google_search": {}  # Simple config; add options like disable_attribution if needed
                    }
                )
            )

    def invoke(self, prompt: str) -> Any:
        try:
            return self.model.generate_content(prompt, tools=self.tools)
        except Exception as e:
            logger.error(f"Error invoking model: {e}")
            raise

    async def async_invoke(self, prompt: str) -> Any:
        # Async version for non-blocking calls (requires async Vertex AI support)
        try:
            return await self.model.generate_content_async(prompt, tools=self.tools)
        except Exception as e:
            logger.error(f"Error in async invoke: {e}")
            raise

    def with_structured_output(self, pydantic_model):
        class StructuredOutputWrapper:
            def __init__(self, outer: "GroundedLLMWrapper"):
                self.outer = outer

            def invoke(self, prompt: str) -> Any:
                prompt_with_instr = build_prompt_with_output_instructions(
                    prompt, pydantic_model
                )
                resp = self.outer.invoke(prompt_with_instr)

                # Extract response text, handling multi-candidate if present
                if hasattr(resp, "candidates") and resp.candidates:
                    response_text = resp.candidates[0].text
                else:
                    response_text = resp.text if hasattr(resp, "text") else str(resp)

                # Strategy 1: Try direct JSON parsing
                try:
                    return pydantic_model.model_validate_json(response_text)
                except Exception as e1:
                    logger.debug(f"JSON parsing failed: {e1}")

                    # Strategy 2: Try parsing as dict/object
                    try:
                        return pydantic_model.model_validate(response_text)
                    except Exception as e2:
                        logger.debug(f"Dict parsing failed: {e2}")

                        # Strategy 3: Try to extract JSON from text with better regex
                        try:
                            json_match = re.search(
                                r"\{(?:[^{}]|(?R))*\}", response_text, re.DOTALL
                            )
                            if json_match:
                                json_str = json_match.group()
                                return pydantic_model.model_validate_json(json_str)
                        except Exception as e3:
                            logger.debug(f"JSON extraction failed: {e3}")

                        # Strategy 4: Fallback - raise error with details instead of empty model
                        logger.error(
                            f"All parsing strategies failed for {pydantic_model.__name__}"
                        )
                        raise ValueError(
                            f"Could not parse response into {pydantic_model.__name__}: {response_text}"
                        )

        return StructuredOutputWrapper(self)


@lru_cache(maxsize=128)
def get_langchain_model(model_name: str = "gemini-2.5-pro") -> GroundedLLMWrapper:
    """
    Get a cached instance of the GroundedLLMWrapper.
    Defaults to Gemini 2.5 Pro for enhanced performance and grounding.
    """
    llm_with_search = GroundedLLMWrapper(model_name)
    return llm_with_search
