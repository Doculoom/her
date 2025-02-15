import datetime
import random
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Request, Header, HTTPException

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.utils.cloud_tasks import reschedule_cloud_task


def get_current_date_time_info():
    tz = ZoneInfo("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    date_str = f"{now.day} {now.strftime('%B')}, {now.year}"
    day_of_week = now.strftime("%A")

    if 5 <= now.hour < 12:
        period = "Morning"
    elif 12 <= now.hour < 17:
        period = "Afternoon"
    elif 17 <= now.hour < 21:
        period = "Evening"
    else:
        period = "Night"

    hour_12 = now.hour % 12 or 12
    suffix = "am" if now.hour < 12 else "pm"
    time_str = f"{period} {hour_12}{suffix}"

    return date_str, day_of_week, time_str


def format_datetime_with_nanoseconds(dt: datetime) -> str:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    dt_pst = dt.astimezone(ZoneInfo("America/Los_Angeles"))

    month_str = dt_pst.strftime("%b")
    day = dt_pst.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    day_str = f"{day}{suffix}"

    hour = dt_pst.hour
    if hour == 0:
        hour_12 = 12
        am_pm = "am"
    elif hour < 12:
        hour_12 = hour
        am_pm = "am"
    elif hour == 12:
        hour_12 = 12
        am_pm = "pm"
    else:
        hour_12 = hour - 12
        am_pm = "pm"

    time_str = f"{hour_12}:{dt_pst.minute:02}{am_pm}"
    return f"{month_str} {day_str}, {time_str}"


def messages_to_string(user_name, messages):
    conversation_string = ""
    for message in messages:
        if isinstance(message, HumanMessage):
            conversation_string += f"{user_name}: {message.content}\n"
        elif isinstance(message, AIMessage):
            conversation_string += f"You: {message.content}\n"
        elif isinstance(message, SystemMessage):
            conversation_string += f"System: {message.content}\n"
    return conversation_string


async def verify_telegram_secret_token(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str, Header()] = None,
):
    token = settings.TELEGRAM_BOT_TOKEN.split(":")[0]
    if x_telegram_bot_api_secret_token != token:
        print(
            f"Forbidden: Invalid secret token. Got: {x_telegram_bot_api_secret_token}"
        )
        raise HTTPException(status_code=403, detail="Forbidden")


def generate_chat_message(sender, user_name, text, ts):
    sender = "you" if sender == "agent" else user_name
    message = f"[{format_datetime_with_nanoseconds(ts)}] {sender}: {text}"
    return message


async def schedule_memory_dump(chat_id: int, user_id: str, user_name: str):
    flush_delay = datetime.timedelta(seconds=settings.MEMORY_DUMP_SECONDS)
    scheduled_time = datetime.datetime.utcnow() + flush_delay
    print(f"Scheduling memory dump at {scheduled_time.time()}")

    payload = {"user_id": user_id, "user_name": user_name}
    task_id = f"summarize_chat_for_{user_id}_on_{chat_id}"

    reschedule_cloud_task(
        payload=payload,
        timestamp=scheduled_time,
        task_type="summarize",
        task_id=task_id,
    )


async def schedule_user_response(chat_id: int, user_id: str, user_name: str):
    delay = random.uniform(3, 5)
    flush_delay = datetime.timedelta(seconds=delay)
    scheduled_time = datetime.datetime.utcnow() + flush_delay
    print(
        f"[{datetime.datetime.utcnow()}] Scheduling response at {scheduled_time.time()}"
    )
    payload = {"chat_id": chat_id, "user_id": user_id, "user_name": user_name}
    task_id = f"respond_to_{user_id}_{chat_id}"

    reschedule_cloud_task(
        payload=payload,
        timestamp=scheduled_time,
        task_type="respond",
        task_id=task_id,
    )
