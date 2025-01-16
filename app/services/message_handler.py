from app.memory.cortex import Cortex
from app.services.llm_services.gemini_service import gemini_service
from app.services.telegram_service import get_file_from_telegram

cortex = Cortex()


async def process_text_message(user_id: str, text: str, prompt: str = None) -> str:
    cortex.add_user_message(user_id, text)
    text = cortex.get_chat_request(user_id)
    resp =  gemini_service.generate_content([prompt, text])
    cortex.add_agent_message(user_id, resp)
    return resp


async def process_image_message(text: str, file_id: str, prompt: str = None) -> str:
    image_bytes = await get_file_from_telegram(file_id)
    if image_bytes:
        if not text:
            text = "Analyze and describe this image."
        return await gemini_service.generate_content_with_image([prompt, text], image_bytes)
    else:
        return "Sorry, I couldn't retrieve the image from Telegram."


async def process_image_url_message(text: str, image_url: str, prompt: str = None) -> str:
    if not text:
        text = "Analyze and describe this image."
    return await gemini_service.generate_content_from_url([prompt, text], image_url)
