"""
News analyzer service for trend analysis and insights from RSS feeds.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import Counter, defaultdict
from dataclasses import dataclass

from ..content.rss_feed_service import RSSFeedService, NewsArticle
from ..utils.rss_utils import extract_news_keywords, extract_companies_from_text

logger = logging.getLogger(__name__)


@dataclass
class TrendData:
    """Represents trending topic data."""

    keyword: str
    count: int
    articles: List[NewsArticle]
    first_seen: str
    last_seen: str
    sources: List[str]
    companies: List[str]
    trend_score: float


@dataclass
class NewsInsight:
    """Represents a news insight or pattern."""

    type: str  # 'trend', 'spike', 'company_mention', 'topic_emergence'
    title: str
    description: str
    confidence: float
    evidence: List[str]
    timestamp: str


class NewsAnalyzer:
    """Service for analyzing news trends and generating insights."""

    def __init__(self):
        """Initialize news analyzer."""
        self.rss_service = RSSFeedService()

    def analyze_trending_topics(
        self, hours: int = 24, min_mentions: int = 3
    ) -> List[TrendData]:
        """
        Analyze trending topics from news feeds.

        Args:
            hours: Number of hours to look back
            min_mentions: Minimum mentions required for a topic to be considered trending

        Returns:
            List of trending topics with data
        """
        try:
            # Get recent articles
            articles = self.rss_service.get_all_recent_articles(hours)
            if not articles:
                return []

            # Extract keywords from all articles
            keyword_articles = defaultdict(list)
            keyword_sources = defaultdict(set)
            keyword_companies = defaultdict(set)

            for article in articles:
                # Extract keywords from title and description
                text = f"{article.title} {article.description}"
                keywords = extract_news_keywords(text)
                companies = extract_companies_from_text(text)

                for keyword in keywords:
                    keyword_articles[keyword].append(article)
                    keyword_sources[keyword].add(article.source)
                    keyword_companies[keyword].update(companies)

            # Create trend data
            trends = []
            for keyword, keyword_article_list in keyword_articles.items():
                if len(keyword_article_list) >= min_mentions:
                    # Calculate trend score
                    trend_score = self._calculate_trend_score(
                        keyword_article_list, hours
                    )

                    # Get date range
                    article_dates = [
                        article.published
                        for article in keyword_article_list
                        if article.published
                    ]
                    first_seen = min(article_dates) if article_dates else ""
                    last_seen = max(article_dates) if article_dates else ""

                    trend = TrendData(
                        keyword=keyword,
                        count=len(keyword_article_list),
                        articles=keyword_article_list,
                        first_seen=first_seen,
                        last_seen=last_seen,
                        sources=list(keyword_sources[keyword]),
                        companies=list(keyword_companies[keyword]),
                        trend_score=trend_score,
                    )
                    trends.append(trend)

            # Sort by trend score
            trends.sort(key=lambda x: x.trend_score, reverse=True)
            return trends

        except Exception as e:
            logger.error(f"Error analyzing trending topics: {e}")
            return []

    def detect_news_spikes(
        self, hours: int = 24, comparison_hours: int = 168
    ) -> List[NewsInsight]:
        """
        Detect spikes in news coverage for specific topics.

        Args:
            hours: Recent period to analyze
            comparison_hours: Historical period to compare against

        Returns:
            List of detected news spikes
        """
        try:
            # Get recent and historical articles
            recent_articles = self.rss_service.get_all_recent_articles(hours)
            historical_articles = self.rss_service.get_all_recent_articles(
                comparison_hours
            )

            if not recent_articles or not historical_articles:
                return []

            # Count keywords in both periods
            recent_keywords = self._count_keywords_in_articles(recent_articles)
            historical_keywords = self._count_keywords_in_articles(historical_articles)

            # Calculate spike ratios
            spikes = []
            for keyword, recent_count in recent_keywords.items():
                historical_count = historical_keywords.get(keyword, 0)

                # Normalize by time period
                recent_rate = recent_count / hours
                historical_rate = historical_count / comparison_hours

                # Detect significant spikes
                if historical_rate > 0:
                    spike_ratio = recent_rate / historical_rate
                    if spike_ratio > 2.0 and recent_count >= 3:  # At least 2x increase
                        insight = NewsInsight(
                            type="spike",
                            title=f"News spike detected: {keyword}",
                            description=f"'{keyword}' mentioned {recent_count} times in last {hours}h vs {historical_count} times in last {comparison_hours}h",
                            confidence=min(spike_ratio / 10.0, 1.0),
                            evidence=[
                                f"Spike ratio: {spike_ratio:.2f}x",
                                f"Recent mentions: {recent_count}",
                            ],
                            timestamp=datetime.now().isoformat(),
                        )
                        spikes.append(insight)

            return sorted(spikes, key=lambda x: x.confidence, reverse=True)

        except Exception as e:
            logger.error(f"Error detecting news spikes: {e}")
            return []

    def analyze_company_mentions(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze company mentions in recent news.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with company mention analysis
        """
        try:
            articles = self.rss_service.get_all_recent_articles(hours)
            if not articles:
                return {}

            company_mentions = Counter()
            company_articles = defaultdict(list)
            company_sources = defaultdict(set)

            for article in articles:
                text = f"{article.title} {article.description}"
                companies = extract_companies_from_text(text)

                for company in companies:
                    company_mentions[company] += 1
                    company_articles[company].append(article)
                    company_sources[company].add(article.source)

            # Create analysis
            analysis = {
                "time_period": f"{hours} hours",
                "total_companies": len(company_mentions),
                "total_mentions": sum(company_mentions.values()),
                "top_companies": [
                    {
                        "company": company,
                        "mentions": count,
                        "sources": list(company_sources[company]),
                        "articles": len(company_articles[company]),
                    }
                    for company, count in company_mentions.most_common(10)
                ],
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing company mentions: {e}")
            return {}

    def suggest_timely_topics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Suggest timely topics based on news trends.

        Args:
            hours: Number of hours to look back

        Returns:
            List of suggested topics
        """
        try:
            # Get trending topics
            trends = self.analyze_trending_topics(hours)

            # Get recent spikes
            spikes = self.detect_news_spikes(hours)

            # Get company mentions
            company_analysis = self.analyze_company_mentions(hours)

            suggestions = []

            # Suggestions from trending topics
            for trend in trends[:5]:  # Top 5 trends
                suggestion = {
                    "type": "trending_topic",
                    "topic": trend.keyword,
                    "reason": f"Trending in news with {trend.count} mentions",
                    "urgency": "high" if trend.trend_score > 0.7 else "medium",
                    "evidence": {
                        "mentions": trend.count,
                        "sources": trend.sources,
                        "companies": trend.companies,
                        "sample_articles": [
                            {
                                "title": article.title,
                                "source": article.source,
                                "url": article.url,
                            }
                            for article in trend.articles[:3]
                        ],
                    },
                    "suggested_angle": self._suggest_topic_angle(
                        trend.keyword, trend.articles
                    ),
                }
                suggestions.append(suggestion)

            # Suggestions from news spikes
            for spike in spikes[:3]:  # Top 3 spikes
                suggestion = {
                    "type": "news_spike",
                    "topic": spike.title.replace("News spike detected: ", ""),
                    "reason": spike.description,
                    "urgency": "high",
                    "evidence": {
                        "confidence": spike.confidence,
                        "details": spike.evidence,
                    },
                    "suggested_angle": f"Breaking down the recent surge in {spike.title.replace('News spike detected: ', '')} news",
                }
                suggestions.append(suggestion)

            # Suggestions from company mentions
            if company_analysis.get("top_companies"):
                top_company = company_analysis["top_companies"][0]
                suggestion = {
                    "type": "company_focus",
                    "topic": f"{top_company['company']} in the news",
                    "reason": f"Most mentioned company with {top_company['mentions']} mentions",
                    "urgency": "medium",
                    "evidence": {
                        "mentions": top_company["mentions"],
                        "sources": top_company["sources"],
                    },
                    "suggested_angle": f"Analysis of {top_company['company']}'s recent developments and their impact",
                }
                suggestions.append(suggestion)

            # Sort by urgency and relevance
            urgency_order = {"high": 3, "medium": 2, "low": 1}
            suggestions.sort(
                key=lambda x: urgency_order.get(x["urgency"], 0), reverse=True
            )

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting timely topics: {e}")
            return []

    def get_news_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get a comprehensive news summary.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with news summary
        """
        try:
            articles = self.rss_service.get_all_recent_articles(hours)
            if not articles:
                return {}

            # Basic statistics
            sources = set(article.source for article in articles)

            # Get trending topics
            trends = self.analyze_trending_topics(hours, min_mentions=2)

            # Get company mentions
            company_analysis = self.analyze_company_mentions(hours)

            # Get recent spikes
            spikes = self.detect_news_spikes(hours)

            summary = {
                "time_period": f"{hours} hours",
                "total_articles": len(articles),
                "sources": len(sources),
                "trending_topics": len(trends),
                "news_spikes": len(spikes),
                "top_trends": [
                    {
                        "keyword": trend.keyword,
                        "mentions": trend.count,
                        "trend_score": trend.trend_score,
                    }
                    for trend in trends[:5]
                ],
                "top_companies": company_analysis.get("top_companies", [])[:5],
                "recent_spikes": [
                    {
                        "topic": spike.title.replace("News spike detected: ", ""),
                        "confidence": spike.confidence,
                    }
                    for spike in spikes[:3]
                ],
                "analysis_timestamp": datetime.now().isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Error generating news summary: {e}")
            return {}

    def get_trending_keywords(
        self, hours: int = 24, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get trending keywords from news articles.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of keywords to return

        Returns:
            List of trending keywords with metadata
        """
        try:
            articles = self.rss_service.get_all_recent_articles(hours)
            if not articles:
                return []

            keyword_count = Counter()
            keyword_articles = defaultdict(list)
            keyword_sources = defaultdict(set)

            for article in articles:
                text = f"{article.title} {article.description}"
                keywords = extract_news_keywords(text)

                for keyword in keywords:
                    keyword_count[keyword] += 1
                    keyword_articles[keyword].append(article)
                    keyword_sources[keyword].add(article.source)

            trending_keywords = []
            for keyword, count in keyword_count.most_common(limit):
                trending_keywords.append(
                    {
                        "keyword": keyword,
                        "count": count,
                        "sources": list(keyword_sources[keyword]),
                        "trend_score": self._calculate_trend_score(
                            keyword_articles[keyword], hours
                        ),
                        "sample_articles": [
                            {"title": article.title, "source": article.source}
                            for article in keyword_articles[keyword][:3]
                        ],
                    }
                )

            return trending_keywords

        except Exception as e:
            logger.error(f"Error getting trending keywords: {e}")
            return []

    def _count_keywords_in_articles(self, articles: List[NewsArticle]) -> Counter:
        """Count keywords in a list of articles."""
        keyword_count = Counter()

        for article in articles:
            text = f"{article.title} {article.description}"
            keywords = extract_news_keywords(text)
            for keyword in keywords:
                keyword_count[keyword] += 1

        return keyword_count

    def _calculate_trend_score(self, articles: List[NewsArticle], hours: int) -> float:
        """
        Calculate trend score for a keyword based on its articles.

        Args:
            articles: List of articles containing the keyword
            hours: Time period being analyzed

        Returns:
            Trend score between 0 and 1
        """
        if not articles:
            return 0.0

        # Factors for trend score:
        # 1. Frequency (number of articles)
        # 2. Recency (recent articles weighted more)
        # 3. Source diversity
        # 4. Time distribution

        frequency_score = min(len(articles) / 10.0, 1.0)  # Normalize to 10 articles

        # Calculate recency score
        now = datetime.now()
        recency_scores = []
        for article in articles:
            try:
                if article.published:
                    article_date = datetime.fromisoformat(
                        article.published.replace("Z", "+00:00")
                    )
                    hours_ago = (now - article_date).total_seconds() / 3600
                    recency_score = max(0, 1 - (hours_ago / hours))
                    recency_scores.append(recency_score)
            except Exception:
                continue

        recency_score = (
            sum(recency_scores) / len(recency_scores) if recency_scores else 0
        )

        # Calculate source diversity score
        sources = set(article.source for article in articles)
        source_diversity_score = min(len(sources) / 5.0, 1.0)  # Normalize to 5 sources

        # Combine scores
        trend_score = (
            frequency_score * 0.4 + recency_score * 0.4 + source_diversity_score * 0.2
        )

        return trend_score

    def _suggest_topic_angle(self, keyword: str, articles: List[NewsArticle]) -> str:
        """Suggest a topic angle based on keyword and articles."""
        if not articles:
            return f"Explore the latest developments in {keyword}"

        # Simple angle suggestions based on keyword
        angles = {
            "ai": "The AI revolution: What's happening now and what's next",
            "artificial intelligence": "AI breakthroughs and their real-world impact",
            "machine learning": "Machine learning trends shaping the future",
            "data science": "Data science innovations and applications",
            "startup": "Startup landscape analysis and emerging opportunities",
            "funding": "Investment trends and what they mean for tech",
            "regulation": "Regulatory changes and their impact on innovation",
            "privacy": "Privacy concerns in the digital age",
            "cybersecurity": "Cybersecurity threats and defensive strategies",
            "agentic ai": "The rise of autonomous AI agents and their implications",
            "automation": "Automation trends and their impact on industries",
        }

        return angles.get(
            keyword.lower(),
            f"Deep dive into {keyword}: trends, challenges, and opportunities",
        )


# Global instance
news_analyzer = NewsAnalyzer()
