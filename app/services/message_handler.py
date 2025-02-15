from datetime import datetime

from langchain_core.messages import AIMessage

from app.memory.cortex import Cortex
from app.services.llm_services.gemini_service import gemini_service
from app.services.telegram_service import get_file_from_telegram, send_telegram_message
from app.utils.cloud_tasks import add_to_cloud_tasks
from app.utils.helper import schedule_memory_dump, schedule_user_response
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
    user_name = user_details.get("first_name", user_details.get("username", user_id))

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    if "photo" in data["message"]:
        system_prompt = PromptGenerator.generate_system_prompt(user_details)
        resp = await process_image_message(data, system_prompt)
        await finish_sending_message(chat_id, user_id, user_name, resp, True)
    else:
        cortex.add_user_message(user_id, user_name, text)
        await schedule_user_response(chat_id, user_id, user_name)


async def respond_to_user(chat_id: int, user_id: str, user_name: str):
    state = converse.invoke(
        {
            "messages": cortex.get_messages(user_id),
            "user_id": user_id,
            "user_name": user_name,
        }
    )

    resp = state["messages"][-1]
    if resp is None or not isinstance(resp, AIMessage):
        print(f"ERROR: Empty response from the model")
        resp = AIMessage(content="I wont be able to respond now, talk later?")

    await finish_sending_message(chat_id, user_id, user_name, resp.content, True)


async def finish_sending_message(chat_id, user_id, user_name, resp, dump=False):
    try:
        send_telegram_message(chat_id, resp)
    except Exception as e:
        print(f"Unable to send the telegram message | error: {e}")
    else:
        try:
            cortex.add_agent_message(user_id, user_name, resp)
        except Exception as e:
            print(f"Unable to add agent message | error: {e}")
        else:
            if dump:
                try:
                    await schedule_memory_dump(chat_id, user_id, user_name)
                except Exception as e:
                    print(f"Unable to schedule memory dump | error: {e}")


async def process_image_message(data: dict, prompt: str = None) -> str:
    photo = data["message"]["photo"][-1]
    text = data["message"].get(
        "caption",
        "Give a short description of the image in less than 2 sentences, start with Image contains",
    )
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
