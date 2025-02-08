import asyncio
from datetime import timedelta

from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends

from app.agents.agent_factory import agent_registry
from app.services.firestore.users_service import FirestoreUserService
from app.services.message_handler import *
from app.services.telegram_service import send_telegram_message
from app.services.vault_service import store_user_channel
from app.utils.cache import locks
from app.utils.helper import verify_telegram_secret_token

router = APIRouter()
user_service = FirestoreUserService()
seen_channels = set()


@router.post("/telegram/webhook", dependencies=[Depends(verify_telegram_secret_token)])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    details = data.get('message', {}).get('from')
    user_id = str(details.get("id"))
    user_name = details.get("first_name")

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        print(f"user_id: {user_id}, user_name: {user_name}, chat_id: {chat_id}")
        key = (str(user_id), chat_id)

        if key not in seen_channels:
            background_tasks.add_task(store_user_channel, user_name, user_id, chat_id)
            seen_channels.add(key)

        background_tasks.add_task(handle_telegram_message, data)

    return {"ok": True}


# @todo: setup distributed locking when we scale
@router.post("/queue")
async def add_to_queue(request: Request):
    try:
        task_data = await request.json()
        if not all(key in task_data for key in ["user_id", "channel_type", "channel_id", "text"]):
            raise HTTPException(status_code=400, detail="Bad request")

        lock_key = (task_data["user_id"], task_data["channel_type"].lower(), task_data["channel_id"])

        if lock_key not in locks:
            locks[lock_key] = asyncio.Lock()
        lock = locks[lock_key]

        async with lock:
            try:
                if task_data["channel_type"].lower() == "telegram":
                    send_telegram_message(int(task_data["channel_id"]), task_data["text"])
            except Exception as e:
                print(f"Error occurred: {e}")
                raise HTTPException(status_code=500, detail=e)

        return {"status": "Message processed and sent"}
    except ValueError as e:
        print(f"Invalid JSON: {e}")
        raise HTTPException(status_code=500, detail=e)


@router.post("/summarize")
async def summarize(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    if not user_name:
        raise HTTPException(status_code=400, detail="Missing user_name")

    background_tasks.add_task(cortex.save_memories_to_vault, str(user_id), user_name)

    return {"ok": True}


@router.post("/chat")
async def chat(background_tasks: BackgroundTasks):
    users = user_service.list_users()
    for user in users:
        user_name = user.get("user_name")
        user_id = user.get("user_id")
        channel_id = user.get("channel_id")
        background_tasks.add_task(agent_registry.get("chat").act, user_name, user_id, channel_id)
    return {"ok": True}


@router.post("/test/schedule")
async def test_schedule(request: Request):
    data = await request.json()
    future_time = datetime.utcnow() + timedelta(seconds=data["seconds"])
    payload = {
        "user_id": "thecourier5",
        "channel_type": "telegram",
        "channel_id": "5819867749",
        "text": f"{datetime.now().strftime('%H:%M:%S')}",
    }

    add_to_cloud_tasks(
        payload=payload,
        timestamp=future_time,
    )
    return {"ok": True}


@router.post("/test/broadcast")
async def test_broadcast(request: Request):
    data = await request.json()
    users = user_service.list_users()

    for user in users:
        payload = {
            "user_id": user["user_id"],
            "channel_type": user["channel_type"],
            "channel_id": user["channel_id"],
            "text": data.get('text').format(user["user_name"])
        }
        add_to_cloud_tasks(payload=payload)

    return {"ok": True}
