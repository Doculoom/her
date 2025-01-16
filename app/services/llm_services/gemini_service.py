import google.generativeai as genai
import aiohttp
from app.core.config import settings


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.MODEL)

    def generate_content(self, content_parts: list, generation_config=None) -> str:
        try:
            if generation_config and isinstance(generation_config, genai.types.GenerationConfig):
                response = self.model.generate_content(
                    content_parts, generation_config=generation_config
                )
            else:
                response = self.model.generate_content(content_parts)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_with_image(
            self, content_parts: list, image_bytes: bytes, generation_config=None
    ) -> str:
        try:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            content_parts.append(image_part)
            if generation_config and isinstance(generation_config, genai.types.GenerationConfig):
                response = self.model.generate_content(
                    content_parts, generation_config=generation_config
                )
            else:
                response = self.model.generate_content(content_parts)
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_from_url(
            self, content_parts: list, image_url: str, generation_config=None
    ) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    return await self.generate_content_with_image(
                        content_parts, image_bytes, generation_config
                    )
                else:
                    print(f"Error fetching image from URL: {resp.status}")
                    return "Sorry, I couldn't retrieve the image from the URL."


gemini_service = GeminiService()
