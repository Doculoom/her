import datetime
from typing import List, Tuple, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from app.services.firestore.base import FirestoreBaseService
from app.utils.helper import generate_chat_message


class FirestoreUserService(FirestoreBaseService):
    def __init__(self):
        super().__init__()
        self.chat_collection = self.db.collection("chat_history")
        self.user_collection = self.db.collection("user_channels")

    def list_users(self) -> List[Dict[str, Any]]:
        query = self.user_collection.stream()
        return [doc.to_dict() for doc in query]

    def add_chat_message(self, user_id: str, message: Dict[str, Any]) -> str:
        message.update({
            "timestamp": datetime.datetime.utcnow(),
            "flushed": False,
        })

        doc_ref = self.chat_collection.document(user_id).collection("messages").document()
        doc_ref.set(message)
        return doc_ref.id

    def get_chat_messages(self, user_id: str, limit: int) -> List[str]:
        messages_ref = self.chat_collection.document(user_id).collection("messages")
        query = (
            messages_ref
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .limit(limit)
        )
        messages = []
        for doc in query.stream():
            doc = doc.to_dict()
            message = generate_chat_message(doc["sender"], doc["name"], doc["content"], doc["timestamp"])
            messages.append(message)

        return messages

    def get_unflushed_chat_messages(self, user_id: str, limit: int = 200) -> List[Tuple[str, BaseMessage]]:
        messages_ref = self.chat_collection.document(user_id).collection("messages")
        query = (
            messages_ref
            .where(filter=FieldFilter("flushed", "==", False))
            .order_by("timestamp", direction=firestore.Query.ASCENDING)
            .limit(limit)
        )

        return [(doc.id, self._convert_to_langchain_message(doc.to_dict()))
                for doc in query.stream()]

    def mark_messages_as_flushed(self, user_id: str, message_ids: List[str]) -> None:
        if not message_ids:
            return

        batch = self.db.batch()
        messages_ref = self.chat_collection.document(user_id).collection("messages")

        for msg_id in message_ids:
            doc_ref = messages_ref.document(msg_id)
            batch.update(doc_ref, {"flushed": True})

        batch.commit()

    @staticmethod
    def _convert_to_langchain_message(data: Dict[str, Any]) -> BaseMessage:
        if data["sender"] == "agent":
            return AIMessage(content=data["content"], name=data["sender"])
        return HumanMessage(content=data["content"], name=data["sender"])
