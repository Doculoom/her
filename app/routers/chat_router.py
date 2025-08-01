from datetime import timedelta, datetime

from langchain_core.prompts import PromptTemplate
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Depends

from app.core.constants import USER_INACTIVE_MESSAGE
from app.core.llm import get_langchain_model
from app.core.prompt_templates import her_agent_template
from app.models.agent_models import HerResponse, ChatAgentState
from app.services.firestore.users_service import FirestoreUserService
from app.services.message_handler import (
    respond_to_user,
    cortex,
    handle_telegram_message,
    initiate_chat,
    finish_sending_message,
)
from app.services.vault_service import store_user_channel
from app.utils.cloud_tasks import add_to_cloud_tasks
from app.utils.helper import verify_telegram_secret_token

router = APIRouter()
user_service = FirestoreUserService()
seen_channels = set()


@router.post("/telegram/webhook", dependencies=[Depends(verify_telegram_secret_token)])
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    details = data.get("message", {}).get("from")
    user_id = str(details.get("id"))
    user_name = details.get("first_name")

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        print(f"user_id: {user_id}, user_name: {user_name}, chat_id: {chat_id}")
        key = (str(user_id), chat_id)

        if key not in seen_channels:
            background_tasks.add_task(store_user_channel, user_name, user_id, chat_id)
            seen_channels.add(key)

        if "entities" in data["message"]:
            if data["message"].get("text") == "/start":
                return {"ok": True}

        background_tasks.add_task(handle_telegram_message, data)

    return {"ok": True}


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


@router.post("/respond")
async def respond(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    chat_id = payload.get("chat_id")
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")
    print(f"Responding to user {user_id}")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    if not user_name:
        raise HTTPException(status_code=400, detail="Missing user_name")

    background_tasks.add_task(respond_to_user, int(chat_id), str(user_id), user_name)

    return {"ok": True}


@router.post("/chat")
async def chat(background_tasks: BackgroundTasks):
    users = user_service.list_users()
    user_ids = [u["user_id"] for u in users]
    limit = 3

    res = user_service.get_user_activity_and_last_agent_check(
        user_ids=user_ids, limit=limit
    )

    for user in users:
        user_name = user.get("user_name")
        user_id = user.get("user_id")
        chat_id = user.get("channel_id")

        if res[user_id]["agent_count"] >= limit:
            if USER_INACTIVE_MESSAGE not in res[user_id]["history"][-1]:
                # await finish_sending_message(
                #     chat_id, user_id, user_name, USER_INACTIVE_MESSAGE, True
                # )
                continue

        state = {
            "user_id": user_id,
            "user_name": user_name,
            "user_channel": chat_id,
            "messages": res[user_id]["history"],
        }

        background_tasks.add_task(initiate_chat, state=ChatAgentState(**state))

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
        task_type="queue",
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
            "text": data.get("text").format(user["user_name"]),
        }
        add_to_cloud_tasks(payload=payload, task_type="queue")

    return {"ok": True}


@router.post("/test/chat")
async def test_chat(request: Request):
    data = await request.json()
    now = datetime.now()
    prompt = PromptTemplate.from_template(her_agent_template)
    p = prompt.invoke(
        {
            "messages": f"{data['role']}: {data['message']}",
            "current_day": now.date().day,
            "current_time": now.time(),
            "current_date": now.date(),
            "first_name": "Vinay",
        }
    )

    llm = get_langchain_model()
    res = llm.with_structured_output(HerResponse).invoke(p)

    return {"ok": True, "response": res.response}
