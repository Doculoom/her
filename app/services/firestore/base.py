from google.cloud import firestore
from app.core.config import settings


class FirestoreBaseService:
    def __init__(self):
        self.db = firestore.Client(
            project=settings.GCP_PROJECT_ID,
            database=settings.VAULT_DB_NAME
        )
