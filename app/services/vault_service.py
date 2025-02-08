import requests

from app.core.config import settings


def store_user_channel(user_name: str, user_id: str, chat_id: str):
    print("Storing/updating user channels")
    payload = {
        "user_name": user_name,
        "user_id": str(user_id),
        "channel_type": "telegram",
        "channel_id": str(chat_id)
    }

    try:
        response = requests.post(settings.VAULT_API_URL + "/api/v1/channels", json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error storing channel: {e}")
