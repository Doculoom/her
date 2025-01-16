from collections import defaultdict


class Cortex:
    def __init__(self):
        self.chat_history = defaultdict(list)

    def add_user_message(self, user_id, msg):
        msg = f"user: {msg}"
        self.chat_history[user_id].append(msg)

    def add_agent_message(self, user_id, msg):
        msg = f"you: {msg}"
        self.chat_history[user_id].append(msg)

    def get_chat_request(self, user_id, top_k=100):
        if user_id not in self.chat_history:
            return ""

        history = self.chat_history[user_id][-top_k:]
        return '\n'.join(history) + "\n you: "
