"""
Telegram Channel Content Source for X-Hive

Scrapes messages from public Telegram channels using Telethon.
Requires Telegram API credentials (api_id, api_hash).
"""

import re
import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetHistoryRequest
    from telethon.errors import FloodWaitError, ChannelPrivateError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ Telethon not installed. Install with: pip install telethon")

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class TelegramChannelSource(BaseContentSource):
    """
    Telegram channel content source using Telethon.
    
    Scrapes messages from public Telegram channels.
    Requires Telegram API credentials (api_id, api_hash).
    
    Features:
    - Async message fetching
    - URL extraction
    - Hashtag parsing
    - Engagement metrics
    - Rate limit handling
    """
    
    # Popular AI/Tech Telegram channels (verified large public channels)
    DEFAULT_CHANNELS = [
        'crypto',                # Crypto news (large public channel)
        'binance',               # Binance official
        'bloomberg',             # Bloomberg
    ]
    
    def __init__(
        self,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        phone: Optional[str] = None,
        session_name: str = "x_hive_telegram",
        channels: Optional[List[str]] = None,
        max_messages: int = 20,
        hours_lookback: int = 24
    ):
        """
        Initialize Telegram source.
        
        Args:
            api_id: Telegram API ID (from my.telegram.org)
            api_hash: Telegram API hash
            phone: Phone number for authentication
            session_name: Session file name
            channels: List of channel usernames (e.g., '@channel')
            max_messages: Max messages per channel
            hours_lookback: How many hours to look back
        """
        
        if not TELETHON_AVAILABLE:
            raise ContentSourceError(
                "Telethon not installed. Install with: pip install telethon"
            )
        
        super().__init__()
        
        # API credentials
        self.api_id = api_id if api_id is not None else self._load_from_env('TELEGRAM_API_ID')
        self.api_hash = api_hash or self._load_from_env('TELEGRAM_API_HASH')
        self.phone = phone or self._load_from_env('TELEGRAM_PHONE')
        
        # Debug logging
        logger.debug(
            f"Telegram credentials check:\n"
            f"   API_ID: {'✅ ' + str(self.api_id) if self.api_id else '❌ Not found'}\n"
            f"   API_HASH: {'✅ ' + self.api_hash[:10] + '...' if self.api_hash else '❌ Not found'}\n"
            f"   PHONE: {'✅ ' + self.phone if self.phone else '❌ Not found'}"
        )
        
        if not self.api_id or not self.api_hash:
            raise ValueError(
                "Telegram API credentials required. "
                "Set TELEGRAM_API_ID, TELEGRAM_API_HASH in .env file. "
                "Get them from https://my.telegram.org/apps"
            )
        
        # Session
        self.session_name = session_name
        self.session_path = Path(f"data/telegram/{session_name}.session")
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Channels
        self.channels = channels or self.DEFAULT_CHANNELS
        self.max_messages = max_messages
        self.hours_lookback = hours_lookback
        
        # Client
        self.client: Optional[TelegramClient] = None
        self._initialized = False
        
        logger.info(f"✅ TelegramChannelSource initialized ({len(self.channels)} channels)")
    
    def _load_from_env(self, key: str) -> Optional:
        """Load config from environment with type conversion"""
        value = os.getenv(key)
        
        if not value:
            return None
        
        # Special handling for TELEGRAM_API_ID (needs to be int)
        if key == 'TELEGRAM_API_ID':
            try:
                return int(value)
            except (ValueError, TypeError):
                logger.error(f"❌ Invalid TELEGRAM_API_ID: {value} (must be integer)")
                return None
        
        return value
    
    def get_source_name(self) -> str:
        """Get source identifier"""
        return "Telegram Channels"
    
    def get_source_type(self) -> str:
        """Get source type"""
        return "telegram"
    
    async def initialize(self) -> None:
        """Initialize Telegram client"""
        
        if self._initialized:
            return
        
        try:
            self.client = TelegramClient(
                str(self.session_path),
                self.api_id,
                self.api_hash
            )
            
            logger.info("🔗 Connecting to Telegram...")
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                logger.warning("⚠️ Telegram authorization pending")
            else:
                logger.info("✅ Telegram client initialized")
            
            self._initialized = True
        
        except Exception as e:
            raise ContentSourceError(f"Failed to initialize Telegram: {e}")
    
    async def fetch_latest(self, limit: int = 10) -> List[ContentItem]:
        """
        Fetch latest messages from Telegram channels.
        
        Args:
            limit: Maximum total items to return
            
        Returns:
            List of ContentItem objects
        """
        
        # Ensure initialized
        if not self._initialized:
            await self.initialize()
        
        all_items = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.hours_lookback)
        
        for channel in self.channels:
            try:
                items = await self._fetch_channel(channel, cutoff_time)
                all_items.extend(items)
                
                logger.debug(f"✅ Fetched {len(items)} messages from {channel}")
                
                # Rate limiting (be nice to Telegram)
                await asyncio.sleep(2)
            
            except FloodWaitError as e:
                logger.warning(f"⏳ Rate limited on {channel}, waiting {e.seconds}s")
                raise RateLimitError(f"Telegram rate limit: {e.seconds}s")
            
            except ChannelPrivateError:
                logger.warning(f"⚠️ Channel {channel} is private or doesn't exist")
                continue
            
            except Exception as e:
                logger.error(f"❌ Failed to fetch {channel}: {e}")
                continue
        
        # Sort by published date (newest first)
        all_items.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        
        # Return top items
        return all_items[:limit]
    
    async def _fetch_channel(
        self,
        channel: str,
        cutoff_time: datetime
    ) -> List[ContentItem]:
        """
        Fetch messages from a single channel.
        
        Args:
            channel: Channel username (e.g., '@channel')
            cutoff_time: Only fetch messages after this time
        
        Returns:
            List of ContentItem objects
        """
        
        try:
            # Get channel entity
            entity = await self.client.get_entity(channel)
            
            # Fetch messages
            messages = await self.client(GetHistoryRequest(
                peer=entity,
                limit=self.max_messages,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            
            items = []
            
            for msg in messages.messages:
                # Skip old messages
                if msg.date < cutoff_time:
                    continue
                
                # Skip empty messages
                if not msg.message:
                    continue
                
                # Parse message
                item = self._parse_message(msg, channel)
                
                if item:
                    items.append(item)
            
            return items
        
        except Exception as e:
            raise ContentSourceError(f"Failed to fetch {channel}: {e}")
    
    def _parse_message(self, msg, channel: str) -> Optional[ContentItem]:
        """
        Parse Telegram message to ContentItem.
        
        Args:
            msg: Telethon message object
            channel: Channel username
        
        Returns:
            ContentItem or None if not relevant
        """
        
        text = msg.message or ""
        
        # Extract URLs
        urls = self._extract_urls(text)
        
        # Skip if no URLs (we want shareable content)
        if not urls:
            return None
        
        # Use first URL as main URL
        main_url = urls[0]
        
        # Extract title (first line or truncated text)
        lines = text.split('\n')
        title = lines[0][:200] if lines else text[:200]
        
        # Ensure we have a title
        if not title.strip():
            title = "Telegram Message"
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        
        # Auto-categorize
        category = self._auto_categorize(text)
        
        # Create item
        return ContentItem(
            title=title,
            url=main_url,
            source_type=self.get_source_type(),
            source_name=channel,
            description=text[:500],  # Truncate
            content=text,
            published_at=msg.date,
            category=category,
            tags=hashtags,
            # Engagement metrics
            relevance_score=self._calculate_relevance(msg),
            engagement_score=self._calculate_engagement(msg)
        )
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s\)\]\}]+'
        return re.findall(url_pattern, text)
    
    def _auto_categorize(self, text: str) -> ContentCategory:
        """Auto-categorize based on keywords"""
        
        text_lower = text.lower()
        
        # AI/ML keywords
        ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'gpt', 'llm', 'neural', 'transformer',
            'chatgpt', 'claude', 'gemini', 'model', 'training', 'dataset'
        ]
        if any(kw in text_lower for kw in ai_keywords):
            return ContentCategory.AI_ML
        
        # Startup
        if any(kw in text_lower for kw in ['startup', 'funding', 'vc', 'investment', 'series']):
            return ContentCategory.STARTUP
        
        # Programming
        if any(kw in text_lower for kw in ['python', 'javascript', 'code', 'github', 'repo', 'open source']):
            return ContentCategory.PROGRAMMING
        
        # Cybersecurity
        if any(kw in text_lower for kw in ['security', 'hack', 'vulnerability', 'exploit', 'malware']):
            return ContentCategory.CYBERSECURITY
        
        # Blockchain
        if any(kw in text_lower for kw in ['blockchain', 'crypto', 'bitcoin', 'ethereum', 'web3']):
            return ContentCategory.BLOCKCHAIN
        
        return ContentCategory.TECH_NEWS
    
    def _calculate_relevance(self, msg) -> float:
        """Calculate relevance score (0-1)"""
        
        score = 0.5  # Base score
        text = msg.message or ""
        
        # Boost if has URLs
        if self._extract_urls(text):
            score += 0.2
        
        # Boost if has hashtags
        if re.findall(r'#\w+', text):
            score += 0.1
        
        # Boost if longer message (more context)
        if len(text) > 200:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_engagement(self, msg) -> float:
        """Calculate engagement score (0-1)"""
        
        # Views (normalize to 0-1)
        views = getattr(msg, 'views', 0) or 0
        view_score = min(views / 10000, 1.0)  # 10k views = max
        
        # Forwards
        forwards = getattr(msg, 'forwards', 0) or 0
        forward_score = min(forwards / 100, 1.0)  # 100 forwards = max
        
        # Weighted average (views more important)
        return (view_score * 0.7) + (forward_score * 0.3)
    
    async def health_check(self) -> bool:
        """Check if Telegram client is connected"""
        
        try:
            if not self._initialized:
                await self.initialize()
            
            return await self.client.is_user_authorized()
        except:
            return False
    
    async def disconnect(self) -> None:
        """Disconnect Telegram client"""
        
        if self.client:
            await self.client.disconnect()
            logger.info("✅ Telegram client disconnected")


# Environment-based instance (for production)
telegram_source = None

if TELETHON_AVAILABLE:
    try:
        telegram_source = TelegramChannelSource()
        logger.info("✅ Telegram source created successfully")
    except ValueError as e:
        logger.warning(f"⚠️ Telegram source disabled: {e}")
        telegram_source = None
    except Exception as e:
        logger.error(f"❌ Failed to create Telegram source: {e}")
        telegram_source = None
else:
    logger.warning("⚠️ Telethon not available - Telegram source disabled")
