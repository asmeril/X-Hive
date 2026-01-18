from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
import os

app = FastAPI(title="X-HIVE Worker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(settings.LOCK_PATH), exist_ok=True)
    os.makedirs(settings.DATA_PATH, exist_ok=True)
    print(f"✅ Worker started | Lock: {settings.LOCK_PATH}")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "worker": "x-hive",
        "lock_path": settings.LOCK_PATH,
        "data_path": settings.DATA_PATH,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=settings.WORKER_PORT)
