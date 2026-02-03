"""
Content Generator with Telegram Approval Workflow
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from telegram_bot import TelegramApprovalBot, ApprovalStatus
from task_queue import TaskQueue, TaskPriority

logger = logging.getLogger(__name__)


class RiskLevel:
    """Content risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContentGenerator:
    """
    Generates post content and manages approval workflow.
    
    Flow:
    1. Generate draft post
    2. Assess risk level
    3. Send to Telegram for approval
    4. If approved → add to TaskQueue
    5. If skipped/timeout → discard
    """
    
    def __init__(self):
        self.telegram_bot: Optional[TelegramApprovalBot] = None
        self.task_queue: Optional[TaskQueue] = None
        logger.info("✅ ContentGenerator initialized")
    
    async def start(self) -> None:
        """Start content generator"""
        # Initialize Telegram bot
        self.telegram_bot = TelegramApprovalBot()
        await self.telegram_bot.start()
        
        # Initialize TaskQueue
        self.task_queue = TaskQueue()
        await self.task_queue.start()
        
        logger.info("🚀 ContentGenerator started")
    
    async def stop(self) -> None:
        """Stop content generator"""
        if self.telegram_bot:
            await self.telegram_bot.stop()
        
        if self.task_queue:
            await self.task_queue.stop()
        
        logger.info("🛑 ContentGenerator stopped")
    
    def assess_risk(self, text: str) -> str:
        """
        Assess content risk level.
        
        Simple heuristic (can be enhanced with AI):
        - HIGH: Contains controversial keywords
        - MEDIUM: Long posts or URLs
        - LOW: Short, simple posts
        """
        
        text_lower = text.lower()
        
        # High-risk keywords
        high_risk_keywords = [
            "politics", "election", "covid", "vaccine",
            "crypto", "nft", "scandal", "controversy",
            "hack", "scam", "illegal", "nsfw"
        ]
        
        if any(keyword in text_lower for keyword in high_risk_keywords):
            return RiskLevel.HIGH
        
        # Medium risk: long posts or contains URLs
        if len(text) > 200 or "http" in text_lower:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    async def create_post_with_approval(
        self,
        text: str,
        auto_skip_high_risk: bool = True,
        timeout_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Create post with Telegram approval workflow.
        
        Args:
            text: Post content
            auto_skip_high_risk: Auto-skip high-risk content
            timeout_seconds: Approval timeout
        
        Returns:
            {
                "status": "posted" | "skipped" | "timeout" | "auto_skipped",
                "draft_id": str,
                "task_id": str | None,
                "risk_level": str
            }
        """
        
        draft_id = str(uuid.uuid4())[:8]
        risk_level = self.assess_risk(text)
        
        logger.info(f"📝 New draft: {draft_id} | Risk: {risk_level}")
        
        # Auto-skip high-risk content
        if auto_skip_high_risk and risk_level == RiskLevel.HIGH:
            logger.warning(f"🔴 Auto-skipped high-risk content: {draft_id}")
            return {
                "status": "auto_skipped",
                "draft_id": draft_id,
                "task_id": None,
                "risk_level": risk_level,
                "reason": "High-risk content auto-skipped"
            }
        
        # Request approval via Telegram
        approval_result = await self.telegram_bot.request_approval(
            draft_id=draft_id,
            text=text,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds
        )
        
        # Handle approval decision
        if approval_result["status"] == ApprovalStatus.APPROVED:
            # Add to TaskQueue
            task_id = await self.task_queue.add_task(
                task_type="post_tweet",
                payload={"text": approval_result["text"]},
                priority=TaskPriority.HIGH
            )
            
            logger.info(f"✅ Draft approved and queued: {draft_id} → Task: {task_id}")
            
            return {
                "status": "posted",
                "draft_id": draft_id,
                "task_id": task_id,
                "risk_level": risk_level,
                "timestamp": approval_result["timestamp"]
            }
        
        elif approval_result["status"] == ApprovalStatus.SKIPPED:
            logger.info(f"⏭️ Draft skipped by user: {draft_id}")
            return {
                "status": "skipped",
                "draft_id": draft_id,
                "task_id": None,
                "risk_level": risk_level
            }
        
        else:  # TIMEOUT or EDITED
            logger.warning(f"⏰ Draft {approval_result['status']}: {draft_id}")
            return {
                "status": approval_result["status"],
                "draft_id": draft_id,
                "task_id": None,
                "risk_level": risk_level
            }
    
    async def generate_daily_posts(
        self,
        target_count: int = 3,
        post_generator_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate daily posts with approval workflow.
        
        Args:
            target_count: Number of posts to generate (default: 3)
            post_generator_func: Custom function to generate post text
        
        Returns:
            {
                "total_generated": int,
                "approved": int,
                "skipped": int,
                "auto_skipped": int,
                "timeout": int,
                "results": list
            }
        """
        
        if not post_generator_func:
            # Default: simple placeholder posts
            post_generator_func = lambda i: f"📊 Daily update #{i+1}\n\nThis is an automated post from X-Hive."
        
        results = []
        stats = {
            "approved": 0,
            "skipped": 0,
            "auto_skipped": 0,
            "timeout": 0
        }
        
        logger.info(f"🎯 Generating {target_count} daily posts...")
        
        for i in range(target_count):
            # Generate post text
            text = post_generator_func(i)
            
            # Request approval
            result = await self.create_post_with_approval(text)
            results.append(result)
            
            # Update stats
            status = result["status"]
            if status in stats:
                stats[status] += 1
            
            # Wait between posts (avoid spam)
            if i < target_count - 1:
                await asyncio.sleep(5)
        
        logger.info(f"✅ Daily posts completed: {stats}")
        
        return {
            "total_generated": target_count,
            **stats,
            "results": results
        }