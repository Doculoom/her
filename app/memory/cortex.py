from app.agents.summary_agent import SummaryAgent
from app.agents.vault_agent import VaultAgent
from app.core.config import settings
from app.services.firestore.users_service import FirestoreUserService

user_service = FirestoreUserService()


class Cortex:
    @staticmethod
    def add_user_message(user_id: str, user_name: str, msg: str):
        user_service.add_chat_message(
            user_id,
            {
                "sender": "user",
                "content": msg,
                "name": user_name,
            },
        )

    @staticmethod
    def add_agent_message(user_id: str, user_name: str, msg: str):
        user_service.add_chat_message(
            user_id,
            {
                "sender": "agent",
                "content": msg,
                "name": user_name,
            },
        )

    @staticmethod
    def get_messages(user_id, last_n=settings.MAX_MESSAGES_PER_USER):
        history = user_service.get_chat_messages(user_id, last_n)
        history = history[::-1]
        print(f"History: {history}")
        return history

    @staticmethod
    def save_memories_to_vault(user_id, user_name):
        print("Saving memories to vault")
        res = user_service.get_unflushed_chat_messages(user_id)
        messages = [item[1] for item in res]

        old_memories_text = VaultAgent().retrieve_memories_list(user_id)
        new_memories = SummaryAgent().generate_memory(user_name, messages)

        new_memories_text = ""

        for i, m in enumerate(new_memories.memories):
            text = f"""- {m.text} \n"""
            new_memories_text += text

        updated_m = SummaryAgent().update_memories(old_memories_text, new_memories_text)

        for m in updated_m.updated_memories:
            if m.memory_id is None or m.memory_id == "None":
                print(f"Creating new memory: {m.updated_memory}")
                VaultAgent().create_memory(user_id, m.updated_memory)
            else:
                print(f"Updating memory: {m.updated_memory}")
                VaultAgent().update_memory(user_id, m.memory_id, m.updated_memory)

        message_ids = [msg[0] for msg in res]
        user_service.mark_messages_as_flushed(user_id, message_ids)
