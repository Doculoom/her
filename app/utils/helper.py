from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Request, Header, HTTPException

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings


def get_current_date_time_info():
    tz = ZoneInfo("America/Los_Angeles")
    now = datetime.now(tz)
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


def format_datetime_with_nanoseconds(dt):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        pass

    month_str = dt.strftime("%b")
    day = dt.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][day % 10 - 1]
    day_str = str(day) + suffix

    hour = dt.hour
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

    time_str = f"{hour_12}:{dt.minute:02}{am_pm}"
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
