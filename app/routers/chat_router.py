import asyncio
import uuid
from http.client import HTTPException

from fastapi import APIRouter, Request, BackgroundTasks

from app.services.message_handler import *
from app.services.telegram_service import send_telegram_message
from app.services.vault_service import store_user_channel
from app.utils.cache import seen_channels, locks
from app.utils.prompts import PromptGenerator

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()
    print(update)
    user_details = update.get('message', {}).get('from')
    user_details["user_channel"] = "Telegram"
    system_prompt = PromptGenerator.generate_system_prompt(user_details)
    user_id = user_details.get("id", "")
    username = user_details.get("username", user_details.get("first_name", uuid.uuid1()) + user_details.get("last_name"))

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        key = (str(username), chat_id)
        if key not in seen_channels:
            background_tasks.add_task(store_user_channel, username, chat_id)
            seen_channels.add(key)

        if "photo" in update["message"]:
            photo = update["message"]["photo"][-1]
            text = update["message"].get("caption", "Give a short description of the image")
            file_id = photo["file_id"]
            reply_text = await process_image_message(text, file_id, system_prompt)
        elif text.startswith("http") and any(text.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            reply_text = await process_image_url_message(text, text, system_prompt)
        else:
            reply_text = await process_text_message(user_id, text, system_prompt)

        add_message_to_queue(user_id, "telegram", chat_id, reply_text)

    return {"ok": True}


# @todo: setup distributed locking when we scale
@router.post("/queue")
async def add_to_queue(request: Request):
    try:
        task_data = await request.json()
        if not all(key in task_data for key in ["user_id", "channel_type", "channel_id", "text"]):
            raise HTTPException()

        lock_key = (task_data["user_id"], task_data["channel_type"].lower(), task_data["channel_id"])

        if lock_key not in locks:
            locks[lock_key] = asyncio.Lock()
        lock = locks[lock_key]

        async with lock:
            try:
                if task_data["channel_type"].lower() == "telegram":
                    send_telegram_message(int(task_data["channel_id"]), task_data["text"])
                else:
                    raise HTTPException()
            except Exception as e:
                print(f"Error occurred: {e}")
                raise HTTPException()

        return {"status": "Message processed and sent"}
    except ValueError as e:
        print(f"Invalid JSON: {e}")
        raise HTTPException()

