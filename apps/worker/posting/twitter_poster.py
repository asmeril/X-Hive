import logging
import os
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load .env from worker directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

try:
    import tweepy
except ImportError:
    logger.error("tweepy not installed. Install with: pip install tweepy")
    tweepy = None


class TwitterPoster:
    """
    Twitter API v2 integration for posting tweets.
    
    Handles:
    - Tweet posting
    - Authentication
    - Error handling
    - Rate limiting
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        """
        Initialize Twitter poster.
        
        Args:
            api_key: Twitter API key (from env if not provided)
            api_secret: Twitter API secret
            access_token: Access token
            access_token_secret: Access token secret
            bearer_token: Bearer token (for v2 API)
        """
        
        if tweepy is None:
            raise ImportError("tweepy is required. Install with: pip install tweepy")
        
        # Get credentials from env
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
        
        # Validate credentials
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError(
                "Twitter API credentials not found. Please set:\n"
                "  TWITTER_API_KEY\n"
                "  TWITTER_API_SECRET\n"
                "  TWITTER_ACCESS_TOKEN\n"
                "  TWITTER_ACCESS_TOKEN_SECRET\n"
                "in .env file"
            )
        
        # Initialize Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True
        )
        
        logger.info("✅ TwitterPoster initialized")
    
    def post_tweet(self, text: str) -> Optional[Dict]:
        """
        Post a tweet.
        
        Args:
            text: Tweet text (max 280 characters)
        
        Returns:
            Tweet data dict with 'id' and 'text', or None if failed
        """
        
        try:
            # Validate tweet length
            if len(text) > 280:
                logger.error(f"❌ Tweet too long: {len(text)}/280 characters")
                return None
            
            # Post tweet
            logger.info(f"📤 Posting tweet ({len(text)} chars): {text[:50]}...")
            
            response = self.client.create_tweet(text=text)
            
            if response.data:
                tweet_id = response.data['id']
                tweet_text = response.data['text']
                
                logger.info(f"✅ Tweet posted! ID: {tweet_id}")
                
                return {
                    'id': str(tweet_id),
                    'text': tweet_text,
                    'url': f"https://twitter.com/user/status/{tweet_id}",
                    'posted_at': datetime.now().isoformat()
                }
            else:
                logger.error("❌ Failed to post tweet: No response data")
                return None
        
        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error: {e}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Unexpected error posting tweet: {e}")
            return None
    
    def delete_tweet(self, tweet_id: str) -> bool:
        """
        Delete a tweet.
        
        Args:
            tweet_id: Twitter tweet ID
        
        Returns:
            Success status
        """
        
        try:
            logger.info(f"🗑️ Deleting tweet: {tweet_id}")
            
            response = self.client.delete_tweet(tweet_id)
            
            if response.data and response.data.get('deleted'):
                logger.info(f"✅ Tweet deleted: {tweet_id}")
                return True
            else:
                logger.error(f"❌ Failed to delete tweet: {tweet_id}")
                return False
        
        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error deleting tweet: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting tweet: {e}")
            return False
    
    def get_tweet(self, tweet_id: str) -> Optional[Dict]:
        """
        Get tweet data including metrics.
        
        Args:
            tweet_id: Twitter tweet ID
        
        Returns:
            Tweet data dict or None
        """
        
        try:
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['created_at', 'public_metrics', 'text']
            )
            
            if response.data:
                tweet = response.data
                
                return {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if hasattr(tweet, 'created_at') and tweet.created_at else None,
                    'metrics': dict(tweet.public_metrics) if hasattr(tweet, 'public_metrics') and tweet.public_metrics else None
                }
            else:
                return None
        
        except tweepy.TweepyException as e:
            logger.error(f"❌ Error fetching tweet {tweet_id}: {e}")
            return None
    
    def verify_credentials(self) -> bool:
        """
        Verify Twitter API credentials.
        
        Returns:
            True if credentials are valid
        """
        
        try:
            # Try to get authenticated user
            user = self.client.get_me()
            
            if user.data:
                username = user.data.username
                user_id = user.data.id
                logger.info(f"✅ Twitter credentials valid. Authenticated as: @{username} (ID: {user_id})")
                return True
            else:
                logger.error("❌ Twitter credentials invalid")
                return False
        
        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter authentication failed: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Unexpected error verifying credentials: {e}")
            return False


# Global instance (will be initialized when needed)
_poster: Optional[TwitterPoster] = None


def get_twitter_poster() -> TwitterPoster:
    """Get or create global TwitterPoster instance"""
    global _poster
    
    if _poster is None:
        _poster = TwitterPoster()
    
    return _poster
