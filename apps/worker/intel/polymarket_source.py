"""
Polymarket Prediction Markets Source

Fetches trending prediction markets from Polymarket API.
Provides future-oriented intelligence and consensus predictions.
"""

import aiohttp
import logging
from typing import List, Optional
from datetime import datetime, timezone

from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory
)

logger = logging.getLogger(__name__)


class PolymarketSource(BaseContentSource):
    """
    Polymarket prediction markets aggregator.
    
    Fetches active markets with predictions and probabilities.
    Provides unique future-oriented intelligence.
    """
    
    API_ENDPOINTS = [
        "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=20&order=volume24hr&dir=desc",
        "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=20&order=volume24hr&dir=desc",
    ]
    
    def __init__(self, limit: int = 15):
        """
        Initialize Polymarket source.
        
        Args:
            limit: Max markets to fetch
        """
        super().__init__()
        self.limit = limit
        
        logger.info(f"✅ PolymarketSource initialized (limit={limit})")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "Polymarket"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch trending prediction markets"""
        
        items = []
        seen_questions = set()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        for endpoint in self.API_ENDPOINTS:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        endpoint,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        if response.status != 200:
                            continue
                        
                        data = await response.json()
                        
                        # Handle events vs markets endpoints
                        markets = []
                        if "/events" in endpoint:
                            for event in data:
                                event_markets = event.get('markets', [])
                                for m in event_markets:
                                    m['_event_title'] = event.get('title', '')
                                    markets.append(m)
                        else:
                            markets = data
                        
                        # Parse markets
                        for market in markets:
                            if len(items) >= self.limit:
                                break
                            
                            question = market.get('question') or market.get('_event_title')
                            if not question or question in seen_questions:
                                continue
                            
                            # Extract prediction probability
                            prediction_text = self._extract_prediction(market)
                            if not prediction_text:
                                continue
                            
                            # Volume
                            volume = market.get('volume24hr') or market.get('volume', 0)
                            try:
                                volume = float(volume)
                            except:
                                volume = 0
                            
                            # Create item
                            item = ContentItem(
                                title=f"{question} → {prediction_text}",
                                url=f"https://polymarket.com/event/{market.get('slug', '')}",
                                source_type='polymarket',
                                source_name='Polymarket Predictions',
                                published_at=datetime.now(timezone.utc),
                                category=ContentCategory.PREDICTION_MARKET,
                                description=f"Market volume: ${volume:,.0f}"
                            )
                            
                            # Higher volume = higher relevance
                            item.relevance_score = min(0.9, 0.5 + (volume / 1000000) * 0.4)
                            item.engagement_score = 0.8  # Prediction markets are highly engaging
                            
                            items.append(item)
                            seen_questions.add(question)
                
                if items:
                    break  # Found data, stop trying endpoints
            
            except Exception as e:
                logger.debug(f"Error fetching from {endpoint}: {e}")
                continue
        
        logger.info(f"✅ Polymarket: Fetched {len(items)} prediction markets")
        return items
    
    def _extract_prediction(self, market: dict) -> Optional[str]:
        """Extract prediction text from market data"""
        
        # Try outcomes + prices
        try:
            outcomes = market.get('outcomes')
            prices = market.get('outcomePrices')
            
            if isinstance(outcomes, str):
                import json
                outcomes = json.loads(outcomes)
            if isinstance(prices, str):
                import json
                prices = json.loads(prices)
            
            if outcomes and prices and len(outcomes) > 0 and len(prices) > 0:
                prob = float(prices[0]) * 100
                if prob > 0:
                    return f"{outcomes[0]} {prob:.1f}%"
        except:
            pass
        
        # Try tokens
        try:
            tokens = market.get('tokens', [])
            if tokens and len(tokens) > 0:
                token = tokens[0]
                price = float(token.get('price', 0))
                outcome = token.get('outcome', 'Yes')
                if price > 0:
                    return f"{outcome} {price*100:.1f}%"
        except:
            pass
        
        return None


# Global instance
polymarket_source = PolymarketSource()
