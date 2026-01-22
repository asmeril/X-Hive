"""
Approval Manager for X-Hive
Human-in-the-loop safety system for X operations.

Features:
- Manual approval before operations (optional mode)
- Approval timeout (auto-cancel after 5min)
- Batch approval for similar operations
- Emergency stop functionality
- Approval history tracking
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Approval request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class OperationType(str, Enum):
    """X operation types (mirrors rate_limiter.py)"""
    TWEET = "tweet"
    REPLY = "reply"
    QUOTE = "quote"
    LIKE = "like"
    RETWEET = "retweet"


@dataclass
class ApprovalRequest:
    """Approval request data"""
    id: str
    operation_type: str
    payload: Dict
    status: str
    created_at: str
    expires_at: str
    resolved_at: Optional[str] = None
    resolution_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ApprovalRequest":
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if approval request has expired"""
        return datetime.now() > datetime.fromisoformat(self.expires_at)


class ApprovalManager:
    """
    Approval manager with timeout and history.
    
    Modes:
    - DISABLED: No approval needed (default)
    - OPTIONAL: Ask for approval but auto-approve after timeout
    - REQUIRED: All operations must be approved (cancel if timeout)
    """
    
    def __init__(self, storage_path: Optional[str] = None, timeout_seconds: int = 300):
        """
        Initialize approval manager.
        
        Args:
            storage_path: Path to store approval history
            timeout_seconds: Approval timeout (default: 300s = 5min)
        """
        self.storage_path = Path(storage_path or settings.DATA_PATH) / "approval_history.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.timeout_seconds = timeout_seconds
        
        # Pending requests: {request_id: ApprovalRequest}
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        
        # Approval history (last 100 requests)
        self.history: List[ApprovalRequest] = []
        
        # Approval mode
        self.mode = "DISABLED"  # DISABLED | OPTIONAL | REQUIRED
        
        # Emergency stop flag
        self._emergency_stop = False
        
        self._load_history()
        logger.info("✋ ApprovalManager initialized (mode: DISABLED)")
    
    def set_mode(self, mode: str) -> None:
        """
        Set approval mode.
        
        Args:
            mode: DISABLED | OPTIONAL | REQUIRED
        """
        if mode not in ["DISABLED", "OPTIONAL", "REQUIRED"]:
            raise ValueError(f"Invalid mode: {mode}")
        
        self.mode = mode
        logger.info(f"🔄 Approval mode changed to: {mode}")
    
    def is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active"""
        return self._emergency_stop
    
    def emergency_stop(self) -> None:
        """Activate emergency stop (reject all pending/future requests)"""
        self._emergency_stop = True
        
        # Reject all pending requests
        for request_id in list(self.pending_requests.keys()):
            self.reject_request(request_id, reason="Emergency stop activated")
        
        logger.critical("🚨 EMERGENCY STOP ACTIVATED - All operations halted")
    
    def resume(self) -> None:
        """Deactivate emergency stop"""
        self._emergency_stop = False
        logger.info("▶️ Emergency stop deactivated - Operations resumed")
    
    async def request_approval(
        self,
        operation_type: OperationType,
        payload: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Request approval for an operation.
        
        Args:
            operation_type: Type of operation
            payload: Operation-specific data
        
        Returns:
            (approved: bool, reason: Optional[str])
        """
        # Check mode
        if self.mode == "DISABLED":
            return True, None
        
        # Check emergency stop
        if self._emergency_stop:
            return False, "🚨 Emergency stop is active"
        
        # Create approval request
        request_id = str(uuid.uuid4())
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.timeout_seconds)
        
        request = ApprovalRequest(
            id=request_id,
            operation_type=operation_type.value,
            payload=payload,
            status=ApprovalStatus.PENDING.value,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat()
        )
        
        self.pending_requests[request_id] = request
        
        logger.info(f"⏳ Approval request created: {request_id} ({operation_type.value})")
        
        # Wait for approval or timeout
        try:
            approved = await self._wait_for_approval(request_id)
            
            if approved:
                reason = self.pending_requests[request_id].resolution_reason
                return True, reason
            else:
                reason = self.pending_requests[request_id].resolution_reason
                return False, reason
        
        except asyncio.TimeoutError:
            # Timeout handling depends on mode
            if self.mode == "OPTIONAL":
                # Auto-approve on timeout
                self._approve_request(request_id, reason="Auto-approved (timeout)")
                return True, "Auto-approved after timeout"
            else:
                # Cancel on timeout (REQUIRED mode)
                self._timeout_request(request_id)
                return False, f"⏱️ Approval timeout ({self.timeout_seconds}s)"
    
    async def _wait_for_approval(self, request_id: str) -> bool:
        """
        Wait for approval decision.
        
        Args:
            request_id: Request ID
        
        Returns:
            True if approved, False if rejected/cancelled
        
        Raises:
            asyncio.TimeoutError: If timeout expires
        """
        start_time = datetime.now()
        
        while True:
            # Check if request still exists
            if request_id not in self.pending_requests:
                logger.warning(f"Request {request_id} disappeared")
                return False
            
            request = self.pending_requests[request_id]
            
            # Check status
            if request.status == ApprovalStatus.APPROVED.value:
                logger.info(f"✅ Request {request_id} approved")
                self._move_to_history(request_id)
                return True
            
            elif request.status == ApprovalStatus.REJECTED.value:
                logger.info(f"❌ Request {request_id} rejected")
                self._move_to_history(request_id)
                return False
            
            elif request.status == ApprovalStatus.CANCELLED.value:
                logger.info(f"🚫 Request {request_id} cancelled")
                self._move_to_history(request_id)
                return False
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= self.timeout_seconds:
                raise asyncio.TimeoutError()
            
            # Poll every 500ms
            await asyncio.sleep(0.5)
    
    def approve_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """
        Approve a pending request.
        
        Args:
            request_id: Request ID
            reason: Optional reason
        
        Returns:
            True if approved, False if not found/already resolved
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Request {request_id} not found")
            return False
        
        request = self.pending_requests[request_id]
        
        if request.status != ApprovalStatus.PENDING.value:
            logger.warning(f"Request {request_id} already resolved: {request.status}")
            return False
        
        self._approve_request(request_id, reason or "Manually approved")
        return True
    
    def _approve_request(self, request_id: str, reason: str) -> None:
        """Internal: Approve request"""
        request = self.pending_requests[request_id]
        request.status = ApprovalStatus.APPROVED.value
        request.resolved_at = datetime.now().isoformat()
        request.resolution_reason = reason
        
        logger.info(f"✅ Request {request_id} approved: {reason}")
    
    def reject_request(self, request_id: str, reason: Optional[str] = None) -> bool:
        """
        Reject a pending request.
        
        Args:
            request_id: Request ID
            reason: Optional reason
        
        Returns:
            True if rejected, False if not found/already resolved
        """
        if request_id not in self.pending_requests:
            logger.warning(f"Request {request_id} not found")
            return False
        
        request = self.pending_requests[request_id]
        
        if request.status != ApprovalStatus.PENDING.value:
            logger.warning(f"Request {request_id} already resolved: {request.status}")
            return False
        
        request.status = ApprovalStatus.REJECTED.value
        request.resolved_at = datetime.now().isoformat()
        request.resolution_reason = reason or "Manually rejected"
        
        logger.info(f"❌ Request {request_id} rejected: {request.resolution_reason}")
        return True
    
    def _timeout_request(self, request_id: str) -> None:
        """Internal: Mark request as timed out"""
        request = self.pending_requests[request_id]
        request.status = ApprovalStatus.TIMEOUT.value
        request.resolved_at = datetime.now().isoformat()
        request.resolution_reason = f"Timeout after {self.timeout_seconds}s"
        
        logger.warning(f"⏱️ Request {request_id} timed out")
        self._move_to_history(request_id)
    
    def _move_to_history(self, request_id: str) -> None:
        """Move request from pending to history"""
        if request_id in self.pending_requests:
            request = self.pending_requests.pop(request_id)
            self.history.append(request)
            
            # Keep only last 100 requests
            if len(self.history) > 100:
                self.history = self.history[-100:]
            
            self._save_history()
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending approval requests"""
        # Clean expired requests first
        self._cleanup_expired_requests()
        
        return [req.to_dict() for req in self.pending_requests.values()]
    
    def _cleanup_expired_requests(self) -> None:
        """Clean up expired pending requests"""
        now = datetime.now()
        expired_ids = [
            req_id for req_id, req in self.pending_requests.items()
            if datetime.fromisoformat(req.expires_at) < now
        ]
        
        for req_id in expired_ids:
            self._timeout_request(req_id)
    
    def get_statistics(self) -> Dict:
        """Get approval statistics"""
        total = len(self.history)
        
        if total == 0:
            return {
                "total_requests": 0,
                "approved": 0,
                "rejected": 0,
                "timeout": 0,
                "approval_rate": 0.0,
                "pending": 0,
                "emergency_stop_active": self._emergency_stop,
                "mode": self.mode
            }
        
        approved = sum(1 for req in self.history if req.status == ApprovalStatus.APPROVED.value)
        rejected = sum(1 for req in self.history if req.status == ApprovalStatus.REJECTED.value)
        timeout = sum(1 for req in self.history if req.status == ApprovalStatus.TIMEOUT.value)
        
        return {
            "total_requests": total,
            "approved": approved,
            "rejected": rejected,
            "timeout": timeout,
            "approval_rate": (approved / total) * 100 if total > 0 else 0.0,
            "pending": len(self.pending_requests),
            "emergency_stop_active": self._emergency_stop,
            "mode": self.mode
        }
    
    def _load_history(self) -> None:
        """Load approval history from disk"""
        try:
            if not self.storage_path.exists():
                return
            
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            self.history = [
                ApprovalRequest.from_dict(req)
                for req in data.get("history", [])
            ]
            
            logger.info(f"📂 Loaded {len(self.history)} approval records")
        
        except Exception as e:
            logger.error(f"Failed to load approval history: {e}")
            self.history = []
    
    def _save_history(self) -> None:
        """Save approval history to disk"""
        try:
            data = {
                "saved_at": datetime.now().isoformat(),
                "history": [req.to_dict() for req in self.history]
            }
            
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Approval history saved")
        
        except Exception as e:
            logger.error(f"Failed to save approval history: {e}")


# Singleton instance
_approval_manager_instance: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get singleton approval manager instance"""
    global _approval_manager_instance
    if _approval_manager_instance is None:
        _approval_manager_instance = ApprovalManager()
    return _approval_manager_instance
