from app.services.llm_services.gemini_service import gemini_service
from app.services.telegram_service import get_file_from_telegram


async def process_text_message(text: str, prompt: str = None) -> str:
    return gemini_service.generate_content(text, prompt)


async def process_image_message(text: str, file_id: str, prompt: str = None) -> str:
    image_bytes = await get_file_from_telegram(file_id)
    if image_bytes:
        if not text:
            text = "Analyze and describe this image."
        return await gemini_service.generate_content_with_image(text, image_bytes, prompt)
    else:
        return "Sorry, I couldn't retrieve the image from Telegram."


async def process_image_url_message(text: str, image_url: str, prompt: str = None) -> str:
    if not text:
        text = "Analyze and describe this image."
    return await gemini_service.generate_content_from_url(text, image_url, prompt)