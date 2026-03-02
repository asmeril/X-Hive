"""Simple FastAPI server for testing approval endpoints"""
import sys
import asyncio

# Windows asyncio fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import approval queue
from approval.approval_queue import approval_queue

app = FastAPI(title="X-Hive Approval API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "X-Hive Approval API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/approval/pending")
async def get_pending():
    """Get all pending content items"""
    try:
        pending = approval_queue.get_pending()
        items = [item.to_dict() for item in pending]
        
        return {
            "status": "success",
            "data": {
                "items": items,
                "total": len(items)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": {"items": [], "total": 0}
        }

@app.post("/approval/approve/{item_id}")
async def approve_item(item_id: str):
    """Approve item"""
    try:
        success = approval_queue.approve(item_id)
        
        if not success:
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        return {
            "status": "success",
            "message": "Item approved successfully",
            "item_id": item_id,
            "action": "approved"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/approval/reject/{item_id}")
async def reject_item(item_id: str):
    """Reject item"""
    try:
        success = approval_queue.reject(item_id)
        
        if not success:
            return {
                "status": "error",
                "message": f"Item not found: {item_id}"
            }
        
        return {
            "status": "success",
            "message": "Item rejected successfully",
            "item_id": item_id,
            "action": "rejected"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    print("🚀 Starting X-Hive Approval API on http://localhost:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765)
