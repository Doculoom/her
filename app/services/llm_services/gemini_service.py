import aiohttp
from google import genai
from google.genai import types
from app.core.config import settings


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.MODEL
        self.google_search_tool = types.Tool(google_search=types.GoogleSearch())

    def _merge_config(self, generation_config: types.GenerateContentConfig | None):
        if generation_config and isinstance(
            generation_config, types.GenerateContentConfig
        ):
            generation_config.tools = [self.google_search_tool]
            return generation_config
        return types.GenerateContentConfig(tools=[self.google_search_tool])

    def generate_content(
        self,
        content_parts: list,
        generation_config: types.GenerateContentConfig | None = None,
    ) -> str:
        try:
            config = self._merge_config(generation_config)
            response = self.client.models.generate_content(
                model=self.model, contents=content_parts, config=config
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_with_image(
        self,
        content_parts: list,
        image_bytes: bytes,
        generation_config: types.GenerateContentConfig | None = None,
    ) -> str:
        try:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            content_parts.append(image_part)
            config = self._merge_config(generation_config)
            response = self.client.models.generate_content(
                model=self.model, contents=content_parts, config=config
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_from_url(
        self,
        content_parts: list,
        image_url: str,
        generation_config: types.GenerateContentConfig | None = None,
    ) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    return await self.generate_content_with_image(
                        content_parts, image_bytes, generation_config
                    )
                print(f"Error fetching image from URL: {resp.status}")
                return "Sorry, I couldn't retrieve the image from the URL."


gemini_service = GeminiService()
