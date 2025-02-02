import datetime
import threading
from collections import defaultdict, deque

from langchain_core.messages import HumanMessage, AIMessage

from app.agents.agent_factory import agent_registry
from app.core.config import settings
from app.utils.cache import chat_buffer, scheduled_tasks
from app.utils.cloud_tasks import reschedule_cloud_task, add_to_cloud_tasks


class Cortex:
    def __init__(self, max_messages: int = settings.MAX_MESSAGES_PER_USER):
        self.chat_history = defaultdict(lambda: deque(maxlen=max_messages))

    def add_user_message(self, user_id: str, user_name: str, msg: str):
        message = HumanMessage(content=msg, name=user_name)
        self.chat_history[user_id].append(message)
        chat_buffer[user_id].append(message)

    def add_agent_message(self, user_id: str, user_name: str, msg: AIMessage):
        self.chat_history[user_id].append(msg)
        chat_buffer[user_id].append(msg)

        threading.Thread(
            target=self.schedule_memory_dump,
            args=(user_id, user_name),
            daemon=True
        ).start()

    def get_messages(self, user_id, last_n=100):
        history = self.chat_history.get(user_id, deque(maxlen=50))
        return list(history)[-last_n:]

    @staticmethod
    def save_memories_to_vault(user_id, user_name):
        messages = chat_buffer[user_id]

        print(f"Messages: {messages}")
        old_memories_text = agent_registry.get("vault").retrieve_all_memories(user_id)
        new_memories = agent_registry.get("summary").generate_memory(user_name, messages)

        print(f"old_memories_text: {old_memories_text}")
        new_memories_text = ''

        for i, m in enumerate(new_memories.memories):
            text = f"""- {m.text} \n"""
            new_memories_text += text

        updated_m = agent_registry.get("summary").update_memories(old_memories_text, new_memories_text)

        for m in updated_m.updated_memories:
            print(f"Memory: {m}")
            if m.memory_id:
                agent_registry.get("vault").update_memory(user_id, m.memory_id, m.updated_memory)
            else:
                agent_registry.get("vault").create_memory(user_id, m.updated_memory)

        chat_buffer[user_id].clear()

    @staticmethod
    def schedule_memory_dump(user_id: str, user_name: str):
        payload = {"user_id": user_id, "user_name": user_name}
        flush_delay = datetime.timedelta(seconds=settings.MEMORY_DUMP_SECONDS)
        scheduled_time = datetime.datetime.utcnow() + flush_delay
        print(f"Scheduling memory dump at {scheduled_time.time()}")

        if user_id in scheduled_tasks:
            existing_task_name = scheduled_tasks[user_id]
            try:
                response = reschedule_cloud_task(
                    existing_task_name,
                    payload,
                    timestamp=scheduled_time,
                    task_type="summarize"
                )
                scheduled_tasks[user_id] = response.name
            except Exception as e:
                print(f"Error rescheduling task for {user_id}: {e}")
        else:
            response = add_to_cloud_tasks(payload, timestamp=scheduled_time, task_type="summarize")
            scheduled_tasks[user_id] = response.name
