import datetime
import threading

from app.agents.agent_factory import agent_registry
from app.core.config import settings
from app.services.firestore.users_service import FirestoreUserService
from app.utils.cache import scheduled_tasks
from app.utils.cloud_tasks import reschedule_cloud_task, add_to_cloud_tasks

user_service = FirestoreUserService()


class Cortex:
    @staticmethod
    def add_user_message(user_id: str, user_name: str, msg: str):
        user_service.add_chat_message(user_id, {
            "sender": "user",
            "content": msg,
            "name": user_name,
        })

    def add_agent_message(self, user_id: str, user_name: str, msg: str):
        user_service.add_chat_message(user_id, {
            "sender": "agent",
            "content": msg,
            "name": user_name,
        })

        threading.Thread(
            target=self.schedule_memory_dump,
            args=(user_id, user_name),
            daemon=True
        ).start()

    @staticmethod
    def get_messages(user_id, last_n=settings.MAX_MESSAGES_PER_USER):
        history = user_service.get_chat_messages(user_id, last_n)
        return history

    @staticmethod
    def save_memories_to_vault(user_id, user_name):
        print("Saving memories to vault")
        res = user_service.get_unflushed_chat_messages(user_id)
        messages = [item[1] for item in res]

        old_memories_text = agent_registry.get("vault").retrieve_memories_text(user_id, ["id", "text"])
        new_memories = agent_registry.get("summary").generate_memory(user_name, messages)

        new_memories_text = ''

        for i, m in enumerate(new_memories.memories):
            text = f"""- {m.text} \n"""
            new_memories_text += text

        updated_m = agent_registry.get("summary").update_memories(old_memories_text, new_memories_text)

        for m in updated_m.updated_memories:
            if m.memory_id:
                agent_registry.get("vault").update_memory(user_id, m.memory_id, m.updated_memory)
            else:
                agent_registry.get("vault").create_memory(user_id, m.updated_memory)

        message_ids = [msg[0] for msg in res]
        user_service.mark_messages_as_flushed(user_id, message_ids)

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
