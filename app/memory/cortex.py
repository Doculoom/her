class Cortex:
    def __init__(self):
        self.chat_history = []

    def add_user_message(self, msg):
        msg = f"user: {msg}"
        self.chat_history.append(msg)

    def add_agent_message(self, msg):
        msg = f"you: {msg}"
        self.chat_history.append(msg)

    def get_chat_request(self, top_k=100):
        history = self.chat_history[-top_k:]
        return '\n'.join(history) + "\n you: "
