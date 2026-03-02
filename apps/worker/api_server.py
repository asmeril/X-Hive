"""
X-Hive Approval API Server
Lightweight FastAPI server for desktop approval interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from approval.approval_queue import ApprovalQueue
import uvicorn
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="X-Hive Approval API",
    description="API for content approval workflow",
    version="1.0.0"
)

# CORS middleware (desktop app için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Approval queue instance
try:
    approval_queue = ApprovalQueue()
    logger.info("✅ ApprovalQueue initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize ApprovalQueue: {e}")
    approval_queue = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "X-Hive Approval API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "x-hive-approval-api",
        "queue_initialized": approval_queue is not None
    }

@app.get("/approval/pending")
async def get_pending_items():
    """Get all pending approval items"""
    if not approval_queue:
        raise HTTPException(status_code=500, detail="Approval queue not initialized")
    
    try:
        items = approval_queue.get_pending()
        logger.info(f"📋 Fetched {len(items)} pending items")
        
        # Convert items to dict format
        items_dict = [item.to_dict() for item in items]
        
        return {
            "status": "success",
            "data": {
                "items": items_dict,
                "total": len(items_dict)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching pending items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approval/approve/{item_id}")
async def approve_item(item_id: str):
    """Approve a pending item"""
    if not approval_queue:
        raise HTTPException(status_code=500, detail="Approval queue not initialized")
    
    try:
        result = approval_queue.approve(item_id)
        
        if not result:
            logger.warning(f"⚠️ Item not found: {item_id}")
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        logger.info(f"✅ Approved item: {item_id}")
        
        return {
            "status": "success",
            "message": "Item approved successfully",
            "item_id": item_id,
            "action": "approved"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error approving item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/approval/reject/{item_id}")
async def reject_item(item_id: str):
    """Reject a pending item"""
    if not approval_queue:
        raise HTTPException(status_code=500, detail="Approval queue not initialized")
    
    try:
        result = approval_queue.reject(item_id)
        
        if not result:
            logger.warning(f"⚠️ Item not found: {item_id}")
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        logger.info(f"❌ Rejected item: {item_id}")
        
        return {
            "status": "success",
            "message": "Item rejected successfully",
            "item_id": item_id,
            "action": "rejected"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error rejecting item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/approval/stats")
async def get_stats():
    """Get approval statistics"""
    if not approval_queue:
        raise HTTPException(status_code=500, detail="Approval queue not initialized")
    
    try:
        pending = approval_queue.get_pending()
        approved = approval_queue.get_approved()
        
        return {
            "status": "success",
            "data": {
                "pending": len(pending),
                "approved": len(approved),
                "total": len(approval_queue.items)
            }
        }
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Start the API server"""
    logger.info("🚀 Starting X-Hive Approval API Server...")
    logger.info("📍 Server will be available at: http://localhost:8765")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )


if __name__ == "__main__":
    main()
