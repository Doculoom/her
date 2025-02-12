from datetime import datetime

from langchain_core.messages import AIMessage

from app.memory.cortex import Cortex
from app.services.llm_services.gemini_service import gemini_service
from app.services.telegram_service import get_file_from_telegram
from app.utils.cloud_tasks import add_to_cloud_tasks
from app.utils.prompts import PromptGenerator
from app.workflows.conversational_workflow import converse

cortex = Cortex()


def add_message_to_queue(
    user_id: str,
    channel_type: str,
    channel_id: str,
    message: str,
    timestamp: datetime = None,
):
    payload = {
        "user_id": user_id,
        "channel_type": channel_type,
        "channel_id": channel_id,
        "text": message,
    }

    response = add_to_cloud_tasks(payload, timestamp)
    return response


async def handle_telegram_message(data):
    user_details = data.get("message", {}).get("from")
    user_details["user_channel"] = "Telegram"

    user_id = str(user_details.get("id"))
    first_name = user_details.get("first_name", user_details.get("username", user_id))

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if "photo" in data["message"]:
        system_prompt = PromptGenerator.generate_system_prompt(user_details)
        reply_text = await process_image_message(data, system_prompt)
    else:
        reply_text = await process_text_message(first_name, user_id, text)

    if reply_text is not None:
        add_message_to_queue(user_id, "telegram", chat_id, reply_text)


async def process_text_message(
    user_name: str, user_id: str, text: str, user_channel: str = "Telegram"
) -> str:
    cortex.add_user_message(user_id, user_name, text)
    new_state = converse.invoke(
        {
            "messages": cortex.get_messages(user_id),
            "user_id": user_id,
            "user_name": user_name,
            "user_channel": user_channel,
        }
    )
    resp = new_state["messages"][-1]

    print(f"resp: {resp}")
    if not isinstance(resp, AIMessage):
        resp = AIMessage(content="I wont be able to respond now, talk later?")

    cortex.add_agent_message(user_id, user_name, resp.content, True)

    return resp.content


async def process_image_message(data: dict, prompt: str = None) -> str:
    photo = data["message"]["photo"][-1]
    text = data["message"].get("caption", "Give a short description of the image")
    file_id = photo["file_id"]
    image_bytes = await get_file_from_telegram(file_id)

    if image_bytes:
        if not text:
            text = "Analyze and describe this image."
        return await gemini_service.generate_content_with_image(
            [prompt, text], image_bytes
        )
    else:
        return "Sorry, I couldn't retrieve the image from Telegram."


async def process_image_url_message(
    text: str, image_url: str, prompt: str = None
) -> str:
    if not text:
        text = "Analyze and describe this image."
    return await gemini_service.generate_content_from_url([prompt, text], image_url)
