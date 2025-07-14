"""
RSS feed service for processing and managing RSS feeds.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from ..config.rss_config import rss_config_manager, FeedConfig
from ..utils.rss_utils import (
    fetch_rss_feed,
    extract_feed_metadata,
    extract_google_alerts_articles,
    extract_standard_rss_articles,
    is_google_alerts_feed,
    extract_news_keywords,
)
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article from an RSS feed."""

    id: str
    title: str
    description: str
    url: str
    published: str
    source: str
    feed_id: str
    keywords: List[str] = None
    sentiment: Optional[str] = None
    companies: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.companies is None:
            self.companies = []


@dataclass
class FeedData:
    """Represents processed RSS feed data."""

    feed_id: str
    feed_name: str
    feed_url: str
    feed_type: str
    metadata: Dict[str, Any]
    articles: List[NewsArticle]
    last_updated: str
    total_articles: int


class RSSFeedService:
    """Service for managing RSS feeds and processing news articles."""

    def __init__(self):
        """Initialize RSS feed service."""
        self.config_manager = rss_config_manager
        self.cache_manager = CacheManager("rss_feeds_cache.json", ttl_hours=1)

    def fetch_feed(
        self, feed_id: str, force_refresh: bool = False
    ) -> Optional[FeedData]:
        """
        Fetch and process an RSS feed.

        Args:
            feed_id: ID of the feed to fetch
            force_refresh: Whether to bypass cache

        Returns:
            Processed feed data or None if error
        """
        try:
            feed_config = self.config_manager.get_feed(feed_id)
            if not feed_config:
                logger.error(f"Feed config not found: {feed_id}")
                return None

            if not feed_config.enabled:
                logger.info(f"Feed disabled: {feed_id}")
                return None

            # Check cache first
            cache_key = f"feed_{feed_id}"
            if not force_refresh:
                cached_data = self.cache_manager.read_cache()
                if cached_data and "data" in cached_data:
                    try:
                        cached_feeds = json.loads(cached_data["data"])
                        if cache_key in cached_feeds:
                            logger.info(f"Using cached data for feed: {feed_id}")
                            return self._deserialize_feed_data(cached_feeds[cache_key])
                    except Exception as e:
                        logger.warning(f"Error reading cache: {e}")

            # Fetch fresh data
            logger.info(
                f"Fetching fresh data for feed: {feed_id} (URL: {feed_config.url})"
            )
            raw_feed = fetch_rss_feed(feed_config.url)
            if not raw_feed:
                logger.error(f"Failed to fetch feed: {feed_id}")
                return None

            # Process feed data
            feed_data = self._process_feed_data(feed_config, raw_feed)

            # Cache the result
            self._cache_feed_data(feed_id, feed_data)

            return feed_data

        except Exception as e:
            logger.error(f"Error fetching feed {feed_id}: {e}")
            return None

    def fetch_all_enabled_feeds(self, force_refresh: bool = False) -> List[FeedData]:
        """
        Fetch all enabled RSS feeds.

        Args:
            force_refresh: Whether to bypass cache

        Returns:
            List of processed feed data
        """
        enabled_feeds = self.config_manager.get_enabled_feeds()
        feed_data_list = []

        for feed_config in enabled_feeds:
            feed_data = self.fetch_feed(feed_config.id, force_refresh)
            if feed_data:
                feed_data_list.append(feed_data)

        return feed_data_list

    def get_recent_articles(self, feed_id: str, hours: int = 24) -> List[NewsArticle]:
        """
        Get recent articles from a specific feed.

        Args:
            feed_id: ID of the feed
            hours: Number of hours to look back

        Returns:
            List of recent articles
        """
        try:
            feed_data = self.fetch_feed(feed_id)
            if not feed_data:
                logger.warning(f"No feed data for {feed_id}")
                return []

            logger.info(f"Feed {feed_id} has {len(feed_data.articles)} total articles")

            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_articles = []
            date_parse_failures = 0

            for article in feed_data.articles:
                try:
                    if not article.published:
                        logger.warning(
                            f"Article has no published date: {article.title}"
                        )
                        # Include articles without dates if looking back more than 24 hours
                        if hours > 24:
                            recent_articles.append(article)
                        continue

                    # Try multiple date parsing approaches
                    article_date = None

                    # Try ISO format first
                    try:
                        article_date = datetime.fromisoformat(
                            article.published.replace("Z", "+00:00")
                        )
                    except Exception:
                        # Try common RSS date formats
                        import email.utils

                        try:
                            timestamp = email.utils.parsedate_to_datetime(
                                article.published
                            )
                            article_date = timestamp
                        except Exception:
                            # If all parsing fails, include the article if looking back more than 24 hours
                            logger.warning(
                                f"Could not parse date '{article.published}' for article: {article.title}"
                            )
                            if hours > 24:
                                recent_articles.append(article)
                            date_parse_failures += 1
                            continue

                    if article_date and article_date >= cutoff_time:
                        recent_articles.append(article)
                    elif article_date:
                        hours_ago = (
                            datetime.now() - article_date.replace(tzinfo=None)
                        ).total_seconds() / 3600
                        logger.debug(
                            f"Article '{article.title}' is {hours_ago:.1f} hours old (cutoff: {hours})"
                        )

                except Exception as e:
                    logger.warning(
                        f"Error processing article date: {e} for article: {article.title}"
                    )
                    # Include articles with date errors if looking back more than 24 hours
                    if hours > 24:
                        recent_articles.append(article)
                    continue

            logger.info(
                f"Found {len(recent_articles)} recent articles (within {hours}h) from {len(feed_data.articles)} total, {date_parse_failures} date parse failures"
            )
            return sorted(
                recent_articles, key=lambda x: x.published or "", reverse=True
            )

        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

    def get_all_recent_articles(self, hours: int = 24) -> List[NewsArticle]:
        """
        Get recent articles from all enabled feeds.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent articles from all feeds
        """
        all_articles = []
        enabled_feeds = self.config_manager.get_enabled_feeds()

        for feed_config in enabled_feeds:
            articles = self.get_recent_articles(feed_config.id, hours)
            all_articles.extend(articles)

        # Sort by publication date
        return sorted(all_articles, key=lambda x: x.published, reverse=True)

    def search_articles(
        self, query: str, feed_id: Optional[str] = None, hours: int = 168
    ) -> List[NewsArticle]:
        """
        Search for articles containing specific keywords.

        Args:
            query: Search query
            feed_id: Specific feed ID to search (optional)
            hours: Number of hours to look back

        Returns:
            List of matching articles
        """
        try:
            if feed_id:
                articles = self.get_recent_articles(feed_id, hours)
            else:
                articles = self.get_all_recent_articles(hours)

            query_lower = query.lower()
            matching_articles = []

            for article in articles:
                # Search in title and description
                title_match = query_lower in article.title.lower()
                desc_match = query_lower in article.description.lower()
                keyword_match = any(
                    query_lower in keyword.lower() for keyword in article.keywords
                )

                if title_match or desc_match or keyword_match:
                    matching_articles.append(article)

            return matching_articles

        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return []

    def get_feed_statistics(self, feed_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a specific feed or all feeds.

        Args:
            feed_id: Specific feed ID (optional)

        Returns:
            Dictionary containing feed statistics
        """
        try:
            if feed_id:
                feed_data = self.fetch_feed(feed_id)
                if not feed_data:
                    return {}

                return {
                    "feed_id": feed_id,
                    "feed_name": feed_data.feed_name,
                    "total_articles": feed_data.total_articles,
                    "articles_24h": len(self.get_recent_articles(feed_id, 24)),
                    "articles_7d": len(self.get_recent_articles(feed_id, 168)),
                    "last_updated": feed_data.last_updated,
                }
            else:
                # Statistics for all feeds
                all_feeds = self.fetch_all_enabled_feeds()
                total_articles = sum(feed.total_articles for feed in all_feeds)

                return {
                    "total_feeds": len(all_feeds),
                    "total_articles": total_articles,
                    "articles_24h": len(self.get_all_recent_articles(24)),
                    "articles_7d": len(self.get_all_recent_articles(168)),
                    "feeds": [
                        {
                            "id": feed.feed_id,
                            "name": feed.feed_name,
                            "articles": feed.total_articles,
                        }
                        for feed in all_feeds
                    ],
                }

        except Exception as e:
            logger.error(f"Error getting feed statistics: {e}")
            return {}

    def _process_feed_data(
        self, feed_config: FeedConfig, raw_feed: Dict[str, Any]
    ) -> FeedData:
        """
        Process raw RSS feed data into structured format.

        Args:
            feed_config: Feed configuration
            raw_feed: Raw RSS feed data

        Returns:
            Processed feed data
        """
        # Extract metadata
        metadata = extract_feed_metadata(raw_feed)

        # Extract articles using appropriate method based on feed type
        if feed_config.type == "google_alerts" or is_google_alerts_feed(
            feed_config.url
        ):
            raw_articles = extract_google_alerts_articles(raw_feed)
        else:
            raw_articles = extract_standard_rss_articles(raw_feed)

        # Convert to NewsArticle objects
        articles = []
        for raw_article in raw_articles:
            article = NewsArticle(
                id=raw_article.get("id", "") or raw_article.get("link", ""),
                title=raw_article.get("title", ""),
                description=raw_article.get("description", "")
                or raw_article.get("summary", ""),
                url=raw_article.get("link", ""),
                published=raw_article.get("published", ""),
                source=raw_article.get("source", "") or metadata.get("title", ""),
                feed_id=feed_config.id,
                keywords=self._extract_keywords(raw_article, feed_config.keywords),
            )
            articles.append(article)

        return FeedData(
            feed_id=feed_config.id,
            feed_name=feed_config.name,
            feed_url=feed_config.url,
            feed_type=feed_config.type,
            metadata=metadata,
            articles=articles,
            last_updated=datetime.now().isoformat(),
            total_articles=len(articles),
        )

    def _extract_keywords(
        self, article: Dict[str, Any], config_keywords: List[str]
    ) -> List[str]:
        """
        Extract keywords from article content.

        Args:
            article: Article data
            config_keywords: Keywords from feed configuration

        Returns:
            List of extracted keywords
        """
        keywords = []
        title = article.get("title", "")
        description = article.get("description", "") or article.get("summary", "")

        # Check for configured keywords (case-insensitive)
        full_text = f"{title} {description}".lower()
        for keyword in config_keywords:
            if keyword.lower() in full_text:
                keywords.append(keyword)

        # Also extract general news keywords for better analysis
        news_keywords = extract_news_keywords(f"{title} {description}", config_keywords)

        # Combine and deduplicate
        all_keywords = list(set(keywords + news_keywords))

        return all_keywords

    def _cache_feed_data(self, feed_id: str, feed_data: FeedData) -> None:
        """
        Cache feed data.

        Args:
            feed_id: Feed ID
            feed_data: Feed data to cache
        """
        try:
            # Read existing cache
            cached_data = self.cache_manager.read_cache()
            cached_feeds = {}

            if cached_data and "data" in cached_data:
                try:
                    cached_feeds = json.loads(cached_data["data"])
                except Exception:
                    cached_feeds = {}

            # Add/update feed data
            cached_feeds[f"feed_{feed_id}"] = self._serialize_feed_data(feed_data)

            # Save cache
            self.cache_manager.write_cache(json.dumps(cached_feeds))

        except Exception as e:
            logger.warning(f"Error caching feed data: {e}")

    def _serialize_feed_data(self, feed_data: FeedData) -> Dict[str, Any]:
        """Serialize feed data for caching."""
        return {
            "feed_id": feed_data.feed_id,
            "feed_name": feed_data.feed_name,
            "feed_url": feed_data.feed_url,
            "feed_type": feed_data.feed_type,
            "metadata": feed_data.metadata,
            "articles": [asdict(article) for article in feed_data.articles],
            "last_updated": feed_data.last_updated,
            "total_articles": feed_data.total_articles,
        }

    def _deserialize_feed_data(self, data: Dict[str, Any]) -> FeedData:
        """Deserialize feed data from cache."""
        articles = [NewsArticle(**article_data) for article_data in data["articles"]]

        return FeedData(
            feed_id=data["feed_id"],
            feed_name=data["feed_name"],
            feed_url=data["feed_url"],
            feed_type=data["feed_type"],
            metadata=data["metadata"],
            articles=articles,
            last_updated=data["last_updated"],
            total_articles=data["total_articles"],
        )

    def refresh_all_feeds(self) -> Dict[str, Any]:
        """
        Refresh all enabled feeds.

        Returns:
            Summary of refresh operation
        """
        try:
            enabled_feeds = self.config_manager.get_enabled_feeds()
            results = {
                "total_feeds": len(enabled_feeds),
                "successful": 0,
                "failed": 0,
                "errors": [],
            }

            for feed_config in enabled_feeds:
                try:
                    feed_data = self.fetch_feed(feed_config.id, force_refresh=True)
                    if feed_data:
                        results["successful"] += 1
                        logger.info(f"Refreshed feed: {feed_config.id}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(
                            f"Failed to refresh feed: {feed_config.id}"
                        )

                except Exception as e:
                    results["failed"] += 1
                    error_msg = f"Error refreshing feed {feed_config.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            return results

        except Exception as e:
            logger.error(f"Error refreshing feeds: {e}")
            return {
                "total_feeds": 0,
                "successful": 0,
                "failed": 0,
                "errors": [f"Error refreshing feeds: {str(e)}"],
            }


# Global instance
rss_feed_service = RSSFeedService()
