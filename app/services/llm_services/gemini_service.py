import vertexai
from vertexai.generative_models import GenerativeModel, Part
import aiohttp
from app.core.config import settings


class GeminiService:
    def __init__(self):
        vertexai.init(
            project=settings.GCP_PROJECT_ID,
            location=settings.GCP_LOCATION,
        )
        self.model = GenerativeModel(settings.MODEL)

    def generate_content(self, text: str, prompt: str = None) -> str:
        try:
            response = self.model.generate_content([prompt, text])
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_with_image(self, text: str, image_bytes: bytes, prompt: str = None) -> str:
        try:
            image_part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
            response = self.model.generate_content([prompt, text, image_part])
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return "Sorry, I encountered an error while processing your request."

    async def generate_content_from_url(self, text: str, image_url: str, prompt: str = None) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    return await self.generate_content_with_image(text, image_bytes, prompt)
                else:
                    print(f"Error fetching image from URL: {resp.status}")
                    return "Sorry, I couldn't retrieve the image from the URL."


gemini_service = GeminiService()