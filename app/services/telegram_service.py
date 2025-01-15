import aiohttp
import requests
from app.core.config import settings


def send_telegram_message(chat_id: int, text: str) -> None:
    url = f"{settings.BASE_TELEGRAM_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error sending message: {response.text}")


async def get_file_from_telegram(file_id: str) -> bytes:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getFile"
    payload = {"file_id": file_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                file_path = (await response.json())["result"]["file_path"]
                file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
                async with session.get(file_url) as file_response:
                    if file_response.status == 200:
                        return await file_response.read()
                    else:
                        print(f"Error downloading file: {file_response.status}")
                        return None
            else:
                print(f"Error getting file info: {response.status}")
                return None