"""
ArXiv Content Source

Fetches latest research papers from ArXiv.org
"""

import arxiv
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from .base_source import (
    BaseContentSource,
    ContentItem,
    ContentCategory,
    ContentSourceError,
    CATEGORY_TARGETS
)
from .cookie_manager import get_cookie_manager

logger = logging.getLogger(__name__)


class ArxivSource(BaseContentSource):
    """
    ArXiv research paper aggregator.
    
    Fetches latest papers from AI/ML and CS categories.
    """
    
    CATEGORIES = {
        'cs.AI': ContentCategory.AI_ML,
        'cs.LG': ContentCategory.AI_ML,
        'cs.CV': ContentCategory.AI_ML,
        'cs.CL': ContentCategory.AI_ML,
        'cs.CR': ContentCategory.SECURITY_PRIVACY,
        'cs.SE': ContentCategory.TECH_PROGRAMMING,
        'physics': ContentCategory.SCIENCE,
        'math': ContentCategory.SCIENCE,
    }
    
    def __init__(
        self,
        categories: Optional[List[str]] = None,
        max_results: int = 20,
        days_back: int = 7
    ):
        super().__init__()
        self.cookie_manager = get_cookie_manager()
        self.categories = categories or list(self.CATEGORIES.keys())
        self.max_results = max_results
        self.days_back = days_back
        
        logger.info(f"✅ ArxivSource initialized ({len(self.categories)} categories)")
    
    def get_source_name(self) -> str:
        """Get source name"""
        return "ArXiv"
    
    async def fetch_latest(self) -> List[ContentItem]:
        """Fetch latest arXiv papers"""
        
        items = []
        
        for category in self.categories:
            try:
                # Search query
                search = arxiv.Search(
                    query=f"cat:{category}",
                    max_results=self.max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )
                
                for paper in search.results():
                    # Filter by date
                    if paper.published < datetime.now() - timedelta(days=self.days_back):
                        continue
                    
                    # Create ContentItem
                    item = ContentItem(
                        title=paper.title,
                        url=paper.entry_id,
                        source_type='arxiv',
                        source_name=f"ArXiv - {category}",
                        published_at=paper.published,
                        author=', '.join([a.name for a in paper.authors[:3]]),
                        description=paper.summary[:500]
                    )
                    
                    # Category
                    item.category = self.CATEGORIES.get(category, ContentCategory.SCIENCE)
                    
                    # Scores (research papers are high quality by default)
                    item.relevance_score = 0.8
                    item.engagement_score = 0.6
                    
                    items.append(item)
                
                logger.info(f"✅ Fetched {len([i for i in items if category in i.source_name])} papers from {category}")
            
            except Exception as e:
                logger.error(f"❌ Error fetching arXiv {category}: {e}")
                continue
        
        return items


# Export
arxiv_source = ArxivSource()
