import faiss
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


class StoreData(BaseModel):
    user_id: str
    convo_chain_id: str
    text: str
    start_timestamp: str
    end_timestamp: str


class QueryData(BaseModel):
    user_id: str
    query_text: str
    distance: float


class Vault:
    def __init__(self):
        self.model = SentenceTransformer("all-mpnet-base-v2")
        self.embedding_length = self.model.get_sentence_embedding_dimension()
        self.database = {}

    def store(self, data):
        if data["user_id"] not in self.database:
            self.database[data["user_id"]] = {
                "embeddings": faiss.IndexFlatL2(self.embedding_length),
                "texts": [],
                "convo_chain_ids": [],
                "start_timestamps": [],
                "end_timestamps": [],
            }

        embedding = self.model.encode(data["text"]).reshape(1, -1)
        self.database[data["user_id"]]["embeddings"].add(embedding)
        self.database[data["user_id"]]["texts"].append(data["text"])
        self.database[data["user_id"]]["convo_chain_ids"].append(data["convo_chain_id"])
        self.database[data["user_id"]]["start_timestamps"].append(data["start_timestamp"])
        self.database[data["user_id"]]["end_timestamps"].append(data["end_timestamp"])

    def query(self, user_id, query_text, distance):
        if user_id not in self.database:
            raise ValueError(f"No data found for user_id: {user_id}")

        query_embedding = np.array(self.model.encode(query_text)).reshape(1, -1)
        lims, distances, indices = self.database[user_id]["embeddings"].range_search(
            query_embedding, distance
        )

        return [
            {
                "text": self.database[user_id]["texts"][index],
                "convo_chain_id": self.database[user_id]["convo_chain_ids"][index],
                "start_timestamp": self.database[user_id]["start_timestamps"][index],
                "end_timestamp": self.database[user_id]["end_timestamps"][index],
            }
            for index in indices
        ]


app = FastAPI()
vault = Vault()


@app.post("/store")
async def store_data(data: StoreData):
    try:
        vault.store(data.dict())
        return {"message": "Data stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_data(data: QueryData):
    try:
        results = vault.query(data.user_id, data.query_text, data.distance)
        return {"results": results}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
