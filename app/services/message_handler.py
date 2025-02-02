from datetime import datetime

from langchain_core.messages import AIMessage

from app.memory.cortex import Cortex
from app.services.llm_services.gemini_service import gemini_service
from app.services.telegram_service import get_file_from_telegram
from app.utils.cloud_tasks import add_to_cloud_tasks
from app.workflows.conversational_workflow import converse

cortex = Cortex()


def add_message_to_queue(
        user_id: str,
        channel_type: str,
        channel_id: str,
        message: str,
        timestamp: datetime = None
):
    payload = {
        "user_id": user_id,
        "channel_type": channel_type,
        "channel_id": channel_id,
        "text": message,
    }

    response = add_to_cloud_tasks(payload, timestamp)
    return response


async def process_text_message(user_name: str, user_id: str, text: str, user_channel: str = "Telegram") -> str:
    cortex.add_user_message(user_id, user_name, text)
    new_state = converse.invoke({
        "messages": cortex.get_messages(user_id),
        "user_id": user_id, "user_name": user_name,
        "user_channel": user_channel
    })

    resp = new_state["messages"][-1]

    if not isinstance(resp, AIMessage):
        resp = AIMessage(content="An error occurred while responding to you")

    cortex.add_agent_message(user_id, user_name, resp)

    return resp.content


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
