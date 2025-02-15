from typing import Optional, Dict, Any
from app.services.firestore.base import FirestoreBaseService


class FirestoreTasksService(FirestoreBaseService):
    def __init__(self):
        super().__init__()
        self.task_collection = self.db.collection("tasks")

    def get_task_mapping(self, task_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.task_collection.document(task_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def set_task_mapping(self, task_id: str, mapping: Dict[str, Any]) -> None:
        self.task_collection.document(task_id).set(mapping)

    def delete_task_mapping(self, task_id: str) -> None:
        self.task_collection.document(task_id).delete()
