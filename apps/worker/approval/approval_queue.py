import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from intel.base_source import ContentItem

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


class ApprovalQueueItem:
    """
    Item in approval queue.
    
    Represents a tweet waiting for manual approval.
    """
    
    def __init__(
        self,
        content_item: ContentItem,
        generated_tweet: str,
        tweet_id: Optional[str] = None,
        status: ApprovalStatus = ApprovalStatus.PENDING,
        created_at: Optional[datetime] = None,
        approved_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ):
        """
        Initialize approval queue item.
        
        Args:
            content_item: Original content item
            generated_tweet: AI-generated tweet text
            tweet_id: Unique ID for this tweet
            status: Approval status
            created_at: When added to queue
            approved_at: When approved/rejected
            notes: User notes
        """
        
        self.content_item = content_item
        self.generated_tweet = generated_tweet
        self.tweet_id = tweet_id or self._generate_id()
        self.status = status
        self.created_at = created_at or datetime.now()
        self.approved_at = approved_at
        self.notes = notes
    
    def _generate_id(self) -> str:
        """Generate unique tweet ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tweet_{timestamp}_{hash(self.generated_tweet) % 10000:04d}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'tweet_id': self.tweet_id,
            'generated_tweet': self.generated_tweet,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'notes': self.notes,
            'content_item': {
                'title': self.content_item.title,
                'url': self.content_item.url,
                'source_name': self.content_item.source_name,
                'source_type': self.content_item.source_type,
                'category': self.content_item.category.value if self.content_item.category else None,
                'quality': self.content_item.quality.value if self.content_item.quality else None,
                'relevance_score': self.content_item.relevance_score,
                'engagement_score': self.content_item.engagement_score,
                'ai_summary': self.content_item.ai_summary
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ApprovalQueueItem':
        """Load from dictionary"""
        # Simplified - full implementation would reconstruct ContentItem
        # For now, create minimal object
        from intel.base_source import ContentItem, ContentCategory, ContentQuality
        
        content_data = data.get('content_item', {})
        content_item = ContentItem(
            title=content_data.get('title', ''),
            url=content_data.get('url', ''),
            source_type=content_data.get('source_type', 'unknown'),
            source_name=content_data.get('source_name', 'Unknown'),
            category=ContentCategory(content_data['category']) if content_data.get('category') else None,
            quality=ContentQuality(content_data['quality']) if content_data.get('quality') else None,
            relevance_score=content_data.get('relevance_score', 0.5),
            engagement_score=content_data.get('engagement_score', 0.5),
        )
        content_item.ai_summary = content_data.get('ai_summary')
        
        return cls(
            content_item=content_item,
            generated_tweet=data['generated_tweet'],
            tweet_id=data['tweet_id'],
            status=ApprovalStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            approved_at=datetime.fromisoformat(data['approved_at']) if data.get('approved_at') else None,
            notes=data.get('notes')
        )


class ApprovalQueue:
    """
    Manages approval queue for AI-generated tweets.
    
    Handles:
    - Adding tweets to queue
    - Approval/rejection
    - Persistence
    - Integration with Telegram bot
    """
    
    def __init__(self, queue_file: str = "data/approval_queue.json"):
        """
        Initialize approval queue.
        
        Args:
            queue_file: Path to queue persistence file
        """
        
        self.queue_file = Path(queue_file)
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.items: Dict[str, ApprovalQueueItem] = {}
        
        # Load existing queue
        self._load()
        
        logger.info(f"✅ ApprovalQueue initialized ({len(self.items)} items)")
    
    def add(self, content_item: ContentItem, generated_tweet: str) -> ApprovalQueueItem:
        """
        Add item to approval queue.
        
        Args:
            content_item: Source content item
            generated_tweet: AI-generated tweet
        
        Returns:
            ApprovalQueueItem
        """
        
        item = ApprovalQueueItem(
            content_item=content_item,
            generated_tweet=generated_tweet
        )
        
        self.items[item.tweet_id] = item
        self._save()
        
        logger.info(f"✅ Added to approval queue: {item.tweet_id}")
        
        return item
    
    def approve(self, tweet_id: str, notes: Optional[str] = None) -> bool:
        """
        Approve a tweet.
        
        Args:
            tweet_id: Tweet ID
            notes: Optional approval notes
        
        Returns:
            Success status
        """
        
        if tweet_id not in self.items:
            logger.error(f"❌ Tweet not found: {tweet_id}")
            return False
        
        item = self.items[tweet_id]
        item.status = ApprovalStatus.APPROVED
        item.approved_at = datetime.now()
        item.notes = notes
        
        self._save()
        
        logger.info(f"✅ Tweet approved: {tweet_id}")
        
        return True
    
    def reject(self, tweet_id: str, reason: Optional[str] = None) -> bool:
        """
        Reject a tweet.
        
        Args:
            tweet_id: Tweet ID
            reason: Optional rejection reason
        
        Returns:
            Success status
        """
        
        if tweet_id not in self.items:
            logger.error(f"❌ Tweet not found: {tweet_id}")
            return False
        
        item = self.items[tweet_id]
        item.status = ApprovalStatus.REJECTED
        item.approved_at = datetime.now()
        item.notes = reason
        
        self._save()
        
        logger.info(f"❌ Tweet rejected: {tweet_id}")
        
        return True
    
    def edit(self, tweet_id: str, new_text: str) -> bool:
        """
        Edit a tweet and mark as edited.
        
        Args:
            tweet_id: Tweet ID
            new_text: New tweet text
        
        Returns:
            Success status
        """
        
        if tweet_id not in self.items:
            logger.error(f"❌ Tweet not found: {tweet_id}")
            return False
        
        item = self.items[tweet_id]
        item.generated_tweet = new_text
        item.status = ApprovalStatus.EDITED
        
        self._save()
        
        logger.info(f"✏️ Tweet edited: {tweet_id}")
        
        return True
    
    def get_pending(self) -> List[ApprovalQueueItem]:
        """Get all pending items"""
        return [
            item for item in self.items.values()
            if item.status == ApprovalStatus.PENDING
        ]
    
    def get_approved(self) -> List[ApprovalQueueItem]:
        """Get all approved items (ready to post)"""
        return [
            item for item in self.items.values()
            if item.status in [ApprovalStatus.APPROVED, ApprovalStatus.EDITED]
        ]
    
    def _save(self):
        """Save queue to file"""
        try:
            data = {
                tweet_id: item.to_dict()
                for tweet_id, item in self.items.items()
            }
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"❌ Failed to save approval queue: {e}")
    
    def _load(self):
        """Load queue from file"""
        try:
            if not self.queue_file.exists():
                return
            
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.items = {
                tweet_id: ApprovalQueueItem.from_dict(item_data)
                for tweet_id, item_data in data.items()
            }
            
            logger.info(f"✅ Loaded {len(self.items)} items from queue")
        
        except Exception as e:
            logger.error(f"❌ Failed to load approval queue: {e}")


# Global instance
approval_queue = ApprovalQueue()
