from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def get_current_date_time_info():
    now = datetime.now()
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
