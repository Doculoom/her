from fastapi import APIRouter, Request

from app.services.message_handler import process_text_message, process_image_message, process_image_url_message
from app.services.telegram_service import send_telegram_message
from app.utils.prompts import PromptGenerator

router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    user_details = update.get('message', {}).get('from')
    user_details["user_channel"] = "Telegram"
    system_prompt = PromptGenerator.generate_system_prompt(user_details)
    print(system_prompt)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if "photo" in update["message"]:
            photo = update["message"]["photo"][-1]
            text = update["message"].get("caption", "Give a short description of the image")
            file_id = photo["file_id"]
            reply_text = await process_image_message(text, file_id, system_prompt)
        elif text.startswith("http") and any(text.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
            reply_text = await process_image_url_message(text, text, system_prompt)
        else:
            reply_text = await process_text_message(text, system_prompt)

        send_telegram_message(chat_id, reply_text)

    return {"ok": True}
