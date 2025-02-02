from collections import deque, defaultdict

from app.core.config import settings

seen_channels = set()
locks = {}
chat_buffer = defaultdict(lambda: deque(maxlen=settings.MAX_MESSAGES_PER_USER))
scheduled_tasks = {}
