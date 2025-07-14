"""
RSS feed MCP tools for news analysis and trend monitoring.
"""

import json
from typing import Optional
from mcp.server.fastmcp import FastMCP
from ..config.rss_config import rss_config_manager
from ..content.rss_feed_service import RSSFeedService
from ..analytics.news_analyzer import NewsAnalyzer


def register_rss_tools(mcp: FastMCP):
    """Register all RSS-related MCP tools."""

    rss_service = RSSFeedService()
    news_analyzer = NewsAnalyzer()

    @mcp.tool()
    def configure_rss_feeds() -> str:
        """
        Get the current RSS feed configuration and instructions for managing feeds.

        Returns:
            str: JSON with current configuration and management instructions
        """
        try:
            config_summary = rss_config_manager.get_config_summary()
            all_feeds = rss_config_manager.get_all_feeds()

            result = {
                "config_summary": config_summary,
                "feeds": [
                    {
                        "id": feed.id,
                        "name": feed.name,
                        "url": feed.url,
                        "type": feed.type,
                        "enabled": feed.enabled,
                        "update_frequency": feed.update_frequency,
                        "keywords": feed.keywords,
                    }
                    for feed in all_feeds
                ],
                "management_instructions": {
                    "add_feed": "To add a new feed, edit the rss_feeds_config.json file in the project root",
                    "enable_disable": "Set the 'enabled' field to true/false in the config file",
                    "update_keywords": "Modify the 'keywords' array in the config file",
                    "config_file_location": config_summary["config_file"],
                },
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error getting RSS configuration: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def get_rss_feeds(enabled_only: bool = True) -> str:
        """
        Get list of configured RSS feeds.

        Args:
            enabled_only (bool): Whether to return only enabled feeds (default: True)

        Returns:
            str: JSON with list of RSS feeds
        """
        try:
            if enabled_only:
                feeds = rss_config_manager.get_enabled_feeds()
            else:
                feeds = rss_config_manager.get_all_feeds()

            result = {
                "total_feeds": len(feeds),
                "enabled_only": enabled_only,
                "feeds": [
                    {
                        "id": feed.id,
                        "name": feed.name,
                        "url": feed.url,
                        "type": feed.type,
                        "enabled": feed.enabled,
                        "update_frequency": feed.update_frequency,
                        "keywords": feed.keywords,
                        "analysis_settings": feed.analysis_settings,
                    }
                    for feed in feeds
                ],
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error getting RSS feeds: {str(e)}"}, indent=2)

    @mcp.tool()
    def fetch_rss_feed(
        feed_id: str, force_refresh: bool = False, debug: bool = False
    ) -> str:
        """
        Fetch and parse a specific RSS feed.

        Args:
            feed_id (str): ID of the feed to fetch
            force_refresh (bool): Whether to bypass cache and fetch fresh data
            debug (bool): Whether to include debug information

        Returns:
            str: JSON with feed data and articles
        """
        try:
            # Get feed config for debugging
            feed_config = rss_config_manager.get_feed(feed_id)
            if not feed_config:
                return json.dumps(
                    {"error": f"Feed configuration not found: {feed_id}"}, indent=2
                )

            feed_data = rss_service.fetch_feed(feed_id, force_refresh)

            if not feed_data:
                debug_info = (
                    {
                        "feed_id": feed_id,
                        "feed_url": feed_config.url,
                        "feed_enabled": feed_config.enabled,
                        "feed_type": feed_config.type,
                    }
                    if debug
                    else {}
                )

                return json.dumps(
                    {
                        "error": f"Feed not found or failed to fetch: {feed_id}",
                        "debug_info": debug_info,
                    },
                    indent=2,
                )

            # Convert to serializable format
            articles = []
            for article in feed_data.articles[:20]:  # Limit to recent 20 articles
                articles.append(
                    {
                        "id": article.id,
                        "title": article.title,
                        "description": article.description[:200] + "..."
                        if len(article.description) > 200
                        else article.description,
                        "url": article.url,
                        "published": article.published,
                        "source": article.source,
                        "keywords": article.keywords,
                        "companies": article.companies,
                    }
                )

            result = {
                "feed_id": feed_data.feed_id,
                "feed_name": feed_data.feed_name,
                "feed_type": feed_data.feed_type,
                "total_articles": feed_data.total_articles,
                "articles_shown": len(articles),
                "last_updated": feed_data.last_updated,
                "articles": articles,
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error fetching RSS feed: {str(e)}"}, indent=2)

    @mcp.tool()
    def analyze_news_trends(hours: int = 24, min_mentions: int = 3) -> str:
        """
        Analyze trending topics from all RSS feeds.

        Args:
            hours (int): Number of hours to look back for trend analysis (default: 24)
            min_mentions (int): Minimum mentions required for a topic to be considered trending (default: 3)

        Returns:
            str: JSON with trending topics analysis
        """
        try:
            trends = news_analyzer.analyze_trending_topics(hours, min_mentions)

            result = {
                "analysis_period": f"{hours} hours",
                "min_mentions_threshold": min_mentions,
                "trending_topics": len(trends),
                "trends": [
                    {
                        "keyword": trend.keyword,
                        "mentions": trend.count,
                        "trend_score": round(trend.trend_score, 3),
                        "sources": trend.sources,
                        "companies": trend.companies,
                        "first_seen": trend.first_seen,
                        "last_seen": trend.last_seen,
                        "sample_articles": [
                            {
                                "title": article.title,
                                "source": article.source,
                                "url": article.url,
                                "published": article.published,
                            }
                            for article in trend.articles[:3]
                        ],
                    }
                    for trend in trends[:10]  # Top 10 trends
                ],
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error analyzing news trends: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def get_trending_keywords(hours: int = 24) -> str:
        """
        Get trending keywords from news feeds.

        Args:
            hours (int): Number of hours to look back (default: 24)

        Returns:
            str: JSON with trending keywords
        """
        try:
            keywords = news_analyzer.get_trending_keywords(hours)

            result = {
                "analysis_period": f"{hours} hours",
                "total_keywords": len(keywords),
                "trending_keywords": keywords,
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error getting trending keywords: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def detect_news_spikes(hours: int = 24, comparison_hours: int = 168) -> str:
        """
        Detect spikes in news coverage for specific topics.

        Args:
            hours (int): Recent period to analyze (default: 24)
            comparison_hours (int): Historical period to compare against (default: 168)

        Returns:
            str: JSON with detected news spikes
        """
        try:
            spikes = news_analyzer.detect_news_spikes(hours, comparison_hours)

            result = {
                "analysis_period": f"{hours} hours vs {comparison_hours} hours",
                "spikes_detected": len(spikes),
                "spikes": [
                    {
                        "topic": spike.title.replace("News spike detected: ", ""),
                        "description": spike.description,
                        "confidence": round(spike.confidence, 3),
                        "evidence": spike.evidence,
                        "timestamp": spike.timestamp,
                    }
                    for spike in spikes[:10]  # Top 10 spikes
                ],
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error detecting news spikes: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def suggest_timely_topics(hours: int = 24) -> str:
        """
        Suggest timely topics based on current news trends.

        Args:
            hours (int): Number of hours to look back for trend analysis (default: 24)

        Returns:
            str: JSON with suggested topics
        """
        try:
            suggestions = news_analyzer.suggest_timely_topics(hours)

            result = {
                "analysis_period": f"{hours} hours",
                "suggestions_count": len(suggestions),
                "suggestions": suggestions,
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error suggesting timely topics: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def get_news_summary(hours: int = 24) -> str:
        """
        Get a comprehensive news summary from all RSS feeds.

        Args:
            hours (int): Number of hours to look back (default: 24)

        Returns:
            str: JSON with news summary
        """
        try:
            summary = news_analyzer.get_news_summary(hours)

            return json.dumps(summary, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error generating news summary: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def search_news_articles(
        query: str, feed_id: Optional[str] = None, hours: int = 168
    ) -> str:
        """
        Search for news articles containing specific keywords.

        Args:
            query (str): Search query/keywords
            feed_id (str, optional): Specific feed ID to search (searches all feeds if not specified)
            hours (int): Number of hours to look back (default: 168)

        Returns:
            str: JSON with matching articles
        """
        try:
            articles = rss_service.search_articles(query, feed_id, hours)

            result = {
                "query": query,
                "feed_id": feed_id or "all_feeds",
                "search_period": f"{hours} hours",
                "results_count": len(articles),
                "articles": [
                    {
                        "title": article.title,
                        "description": article.description[:200] + "..."
                        if len(article.description) > 200
                        else article.description,
                        "url": article.url,
                        "published": article.published,
                        "source": article.source,
                        "feed_id": article.feed_id,
                        "keywords": article.keywords,
                    }
                    for article in articles[:20]  # Limit to 20 results
                ],
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error searching news articles: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def get_company_mentions(hours: int = 24) -> str:
        """
        Analyze company mentions in recent news articles.

        Args:
            hours (int): Number of hours to look back (default: 24)

        Returns:
            str: JSON with company mention analysis
        """
        try:
            analysis = news_analyzer.analyze_company_mentions(hours)

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error analyzing company mentions: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def refresh_all_feeds() -> str:
        """
        Refresh all enabled RSS feeds to get latest articles.

        Returns:
            str: JSON with refresh operation results
        """
        try:
            results = rss_service.refresh_all_feeds()

            return json.dumps(results, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Error refreshing feeds: {str(e)}"}, indent=2)

    @mcp.tool()
    def get_feed_statistics(feed_id: Optional[str] = None) -> str:
        """
        Get statistics for RSS feeds.

        Args:
            feed_id (str, optional): Specific feed ID to get stats for (gets all feeds if not specified)

        Returns:
            str: JSON with feed statistics
        """
        try:
            stats = rss_service.get_feed_statistics(feed_id)

            return json.dumps(stats, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error getting feed statistics: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def debug_rss_feed(feed_id: str) -> str:
        """
        Debug RSS feed connectivity and parsing issues.

        Args:
            feed_id (str): ID of the feed to debug

        Returns:
            str: JSON with detailed debug information
        """
        try:
            from ..utils.rss_utils import fetch_rss_feed

            # Get feed configuration
            feed_config = rss_config_manager.get_feed(feed_id)
            if not feed_config:
                return json.dumps(
                    {"error": f"Feed configuration not found: {feed_id}"}, indent=2
                )

            debug_info = {
                "feed_id": feed_id,
                "feed_name": feed_config.name,
                "feed_url": feed_config.url,
                "feed_type": feed_config.type,
                "feed_enabled": feed_config.enabled,
                "feed_keywords": feed_config.keywords,
                "connectivity_test": "starting...",
                "parsing_test": "pending...",
                "articles_found": 0,
                "error_details": None,
            }

            # Test connectivity
            try:
                raw_feed = fetch_rss_feed(feed_config.url)
                if raw_feed:
                    debug_info["connectivity_test"] = "success"
                    debug_info["feed_title"] = getattr(
                        raw_feed.feed, "title", "No title"
                    )
                    debug_info["feed_description"] = getattr(
                        raw_feed.feed, "description", "No description"
                    )
                    debug_info["total_entries"] = len(getattr(raw_feed, "entries", []))

                    # Test parsing
                    if hasattr(raw_feed, "entries") and raw_feed.entries:
                        debug_info["parsing_test"] = "success"
                        debug_info["articles_found"] = len(raw_feed.entries)

                        # Sample first article
                        first_entry = raw_feed.entries[0]
                        debug_info["sample_article"] = {
                            "title": getattr(first_entry, "title", "No title"),
                            "published": getattr(first_entry, "published", "No date"),
                            "link": getattr(first_entry, "link", "No link"),
                            "description": getattr(
                                first_entry, "description", "No description"
                            )[:200],
                        }

                        # Test keyword matching
                        sample_text = f"{debug_info['sample_article']['title']} {debug_info['sample_article']['description']}"
                        matched_keywords = []
                        for keyword in feed_config.keywords:
                            if keyword.lower() in sample_text.lower():
                                matched_keywords.append(keyword)
                        debug_info["keyword_matching"] = {
                            "configured_keywords": feed_config.keywords,
                            "matched_in_sample": matched_keywords,
                            "sample_text_preview": sample_text[:300],
                        }
                    else:
                        debug_info["parsing_test"] = "failed - no entries found"
                else:
                    debug_info["connectivity_test"] = "failed"
                    debug_info["error_details"] = "Failed to fetch RSS feed"

            except Exception as e:
                debug_info["connectivity_test"] = "failed"
                debug_info["error_details"] = str(e)

            return json.dumps(debug_info, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error debugging RSS feed: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def analyze_feed_keywords(feed_id: str, hours: int = 168) -> str:
        """
        Analyze keyword matching for a specific RSS feed.

        Args:
            feed_id (str): ID of the feed to analyze
            hours (int): Number of hours to look back (default: 168 = 1 week)

        Returns:
            str: JSON with detailed keyword analysis
        """
        try:
            from ..utils.rss_utils import extract_news_keywords

            # Get feed configuration
            feed_config = rss_config_manager.get_feed(feed_id)
            if not feed_config:
                return json.dumps(
                    {"error": f"Feed configuration not found: {feed_id}"}, indent=2
                )

            # Get recent articles
            articles = rss_service.get_recent_articles(feed_id, hours)

            analysis = {
                "feed_id": feed_id,
                "feed_name": feed_config.name,
                "configured_keywords": feed_config.keywords,
                "analysis_period": f"{hours} hours",
                "total_articles": len(articles),
                "keyword_analysis": {},
                "article_details": [],
            }

            # Analyze each configured keyword
            for keyword in feed_config.keywords:
                matching_articles = []
                for article in articles:
                    text = f"{article.title} {article.description}".lower()
                    if keyword.lower() in text:
                        matching_articles.append(
                            {
                                "title": article.title,
                                "published": article.published,
                                "source": article.source,
                                "url": article.url,
                            }
                        )

                analysis["keyword_analysis"][keyword] = {
                    "matches": len(matching_articles),
                    "articles": matching_articles,
                }

            # Analyze all articles for ANY keywords
            for i, article in enumerate(articles[:10]):  # Limit to 10 for readability
                text = f"{article.title} {article.description}"

                # Check configured keywords
                matched_configured = []
                for keyword in feed_config.keywords:
                    if keyword.lower() in text.lower():
                        matched_configured.append(keyword)

                # Extract all possible keywords
                all_keywords = extract_news_keywords(text)

                analysis["article_details"].append(
                    {
                        "index": i + 1,
                        "title": article.title,
                        "published": article.published,
                        "matched_configured_keywords": matched_configured,
                        "all_extracted_keywords": all_keywords,
                        "text_preview": text[:300] + "..." if len(text) > 300 else text,
                    }
                )

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error analyzing feed keywords: {str(e)}"}, indent=2
            )

    @mcp.tool()
    def get_all_feed_articles(feed_id: str, limit: int = 20) -> str:
        """
        Get ALL articles from a feed regardless of date (for debugging).

        Args:
            feed_id (str): ID of the feed to analyze
            limit (int): Maximum number of articles to return (default: 20)

        Returns:
            str: JSON with all articles and their details
        """
        try:
            # Get feed data directly
            feed_data = rss_service.fetch_feed(feed_id, force_refresh=True)

            if not feed_data:
                return json.dumps(
                    {"error": f"Could not fetch feed: {feed_id}"}, indent=2
                )

            # Get feed configuration for keyword checking
            feed_config = rss_config_manager.get_feed(feed_id)

            result = {
                "feed_id": feed_id,
                "feed_name": feed_data.feed_name,
                "total_articles": len(feed_data.articles),
                "articles_shown": min(limit, len(feed_data.articles)),
                "configured_keywords": feed_config.keywords if feed_config else [],
                "articles": [],
            }

            for i, article in enumerate(feed_data.articles[:limit]):
                # Check which keywords match
                full_text = f"{article.title} {article.description}".lower()
                matched_keywords = []
                if feed_config:
                    for keyword in feed_config.keywords:
                        if keyword.lower() in full_text:
                            matched_keywords.append(keyword)

                article_info = {
                    "index": i + 1,
                    "title": article.title,
                    "description": article.description[:200] + "..."
                    if len(article.description) > 200
                    else article.description,
                    "published": article.published,
                    "url": article.url,
                    "source": article.source,
                    "keywords_assigned": article.keywords,
                    "keywords_matched": matched_keywords,
                    "text_preview": full_text[:300] + "..."
                    if len(full_text) > 300
                    else full_text,
                }

                result["articles"].append(article_info)

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps(
                {"error": f"Error getting all feed articles: {str(e)}"}, indent=2
            )
