from fastapi import FastAPI
from app.routers import chat_router

app = FastAPI(title="Her Service", version="1.0.0")

app.include_router(chat_router.router, prefix="/api/v1", tags=["chat"])


@app.get("/health")
def health_check():
    return {"status": "OK"}
