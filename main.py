import json
import os
from collections import defaultdict
from typing import TypedDict

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INTERLOCUTOR_PROMPT_PATH = "interlocutor_prompt.txt"
CONSOLIDATOR_PROMPT_PATH = "consolidator_prompt.txt"
MAX_WORKING_MEMORY_CHARS = 5000
MAX_SHORT_TERM_MEMORY_CHARS = 5000

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

try:
    with open(INTERLOCUTOR_PROMPT_PATH, "r", encoding="utf-8") as f:
        interlocutor_prompt = f.read()
    with open(CONSOLIDATOR_PROMPT_PATH, "r", encoding="utf-8") as f:
        consolidator_prompt = f.read()
except FileNotFoundError as exc:
    raise RuntimeError(f"Prompt file not found: {exc.filename}") from exc

interlocutor = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp", system_instruction=interlocutor_prompt
)
consolidator = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp", system_instruction=consolidator_prompt
)

app = FastAPI()


class UserMessage(BaseModel):
    user_id: str
    text: str


class Summary(TypedDict):
    summary: str
    message_numbers: list[int]


class Cortex:
    def __init__(
        self,
        max_working_chars: int = MAX_WORKING_MEMORY_CHARS,
        max_short_term_chars: int = MAX_SHORT_TERM_MEMORY_CHARS,
    ) -> None:
        self.working_memory: list[dict[str, str]] = []
        self.max_working_memory_chars: int = max_working_chars
        self.current_working_memory_chars: int = 0

        self.short_term_memory: list[str] = []
        self.max_short_term_memory_chars: int = max_short_term_chars
        self.current_short_term_memory_chars: int = 0

    def record_message(self, message: dict[str, str]) -> None:
        self.working_memory.append(message)
        self.current_working_memory_chars += len(message["parts"])
        self._consolidate_working_memory_if_needed()

    def get_prompt(self) -> str:
        short_term_memory_str = "\n".join(self.short_term_memory)
        working_memory_str = "\n".join(
            f"{msg['role']}: {msg['parts']}" for msg in self.working_memory
        )
        return (
            f"Short-term memory:\n{short_term_memory_str}\n\n"
            f"Conversation chain:\n{working_memory_str}"
        )

    def _consolidate_working_memory_if_needed(self) -> None:
        if self.current_working_memory_chars < self.max_working_memory_chars:
            return

        formatted_chat = "\n".join(
            f"<{i:02}> {msg['role']}: {msg['parts']}" for i, msg in enumerate(self.working_memory)
        )

        try:
            response = consolidator.generate_content(
                formatted_chat,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=list[Summary],
                ),
            )
        except Exception as e:
            print(f"[ERROR] Error during working memory consolidation: {e}")
            return

        try:
            summaries: list[Summary] = json.loads(response.text)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Could not decode consolidator response as JSON: {e}")
            return

        indices_to_remove = set()
        for summary in summaries:
            indices_to_remove.update(summary["message_numbers"])
            self.short_term_memory.append(summary["summary"])
            self.current_short_term_memory_chars += len(summary["summary"])

        self.working_memory = [
            msg for i, msg in enumerate(self.working_memory) if i not in indices_to_remove
        ]

        self.current_working_memory_chars = sum(len(msg["parts"]) for msg in self.working_memory)
        self._consolidate_short_term_memory_if_needed()

    def _consolidate_short_term_memory_if_needed(self) -> None:
        if self.current_short_term_memory_chars < self.max_short_term_memory_chars:
            return

        raise NotImplementedError("Long-term memory consolidation is not implemented.")


user_chats: dict[str, Cortex] = defaultdict(lambda: Cortex())


@app.post("/send_message")
def send_message(payload: UserMessage) -> dict[str, str]:
    user_id = payload.user_id.strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID must not be empty.")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    user_chats[user_id].record_message({"role": "user", "parts": text})

    prompt = user_chats[user_id].get_prompt()
    try:
        response = interlocutor.generate_content(contents=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {e}")

    user_chats[user_id].record_message({"role": "model", "parts": response.text})

    return {"model_response": response.text}
