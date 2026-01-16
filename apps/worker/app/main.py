from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import time
import logging

logging.basicConfig(level=logging. INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="X-HIVE Worker")

# CORS for Tauri (localhost:1420)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "https://tauri. localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()

@app.get("/health")
def health_check():
    logger.info("Health check received")
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/status")
def get_status():
    uptime = int(time.time() - start_time)
    return {
        "uptime": uptime,
        "last_job": None,
        "queue_size": 0
    }
