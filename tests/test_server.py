"""
Tests for the RSS News Analyzer MCP Server.
"""

import pytest
import json
import os
import sys
from unittest.mock import Mock, patch

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config.rss_config import RSSConfigManager, FeedConfig
from utils.rss_utils import extract_news_keywords, extract_companies_from_text
from content.rss_feed_service import RSSFeedService
from analytics.news_analyzer import NewsAnalyzer


class TestRSSConfigManager:
    """Test RSS configuration management."""

    def test_feed_config_creation(self):
        """Test creating a feed configuration."""
        feed = FeedConfig(
            id="test_feed",
            name="Test Feed",
            url="https://example.com/feed.xml",
            type="standard_rss",
            keywords=["test", "news"],
            enabled=True,
        )

        assert feed.id == "test_feed"
        assert feed.name == "Test Feed"
        assert feed.url == "https://example.com/feed.xml"
        assert feed.type == "standard_rss"
        assert feed.keywords == ["test", "news"]
        assert feed.enabled is True

    def test_feed_config_defaults(self):
        """Test default values for feed configuration."""
        feed = FeedConfig(
            id="test_feed", name="Test Feed", url="https://example.com/feed.xml"
        )

        assert feed.type == "standard_rss"
        assert feed.keywords == []
        assert feed.update_frequency == "1h"
        assert feed.enabled is True
        assert feed.analysis_settings == {}

    @patch("config.rss_config.os.path.exists")
    @patch("builtins.open")
    def test_config_manager_load_config(self, mock_open, mock_exists):
        """Test loading configuration from file."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
            {
                "feeds": [
                    {
                        "id": "test_feed",
                        "name": "Test Feed",
                        "url": "https://example.com/feed.xml",
                        "type": "standard_rss",
                        "keywords": ["test"],
                        "enabled": True,
                        "update_frequency": "1h",
                        "analysis_settings": {},
                    }
                ]
            }
        )

        manager = RSSConfigManager("test_config.json")
        feeds = manager.get_all_feeds()

        assert len(feeds) == 1
        assert feeds[0].id == "test_feed"
        assert feeds[0].name == "Test Feed"


class TestRSSUtils:
    """Test RSS utility functions."""

    def test_extract_news_keywords(self):
        """Test keyword extraction from text."""
        text = "New AI breakthrough in machine learning and artificial intelligence research"
        keywords = extract_news_keywords(text)

        assert "ai" in keywords
        assert "machine learning" in keywords
        assert "artificial intelligence" in keywords

    def test_extract_companies_from_text(self):
        """Test company extraction from text."""
        text = "Google and Microsoft announce new AI partnership while Apple works on privacy features"
        companies = extract_companies_from_text(text)

        assert "Google" in companies
        assert "Microsoft" in companies
        assert "Apple" in companies

    def test_extract_news_keywords_with_predefined(self):
        """Test keyword extraction with predefined keywords."""
        text = "Latest updates on machine learning algorithms"
        predefined = ["machine learning", "algorithms", "updates"]
        keywords = extract_news_keywords(text, predefined)

        assert "machine learning" in keywords
        assert "algorithms" in keywords
        assert "updates" in keywords


class TestRSSFeedService:
    """Test RSS feed service functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = RSSFeedService()

    @patch("content.rss_feed_service.rss_config_manager")
    def test_fetch_feed_not_found(self, mock_config_manager):
        """Test fetching a non-existent feed."""
        mock_config_manager.get_feed.return_value = None

        service = RSSFeedService()
        result = service.fetch_feed("nonexistent_feed")

        assert result is None

    @patch("content.rss_feed_service.rss_config_manager")
    def test_fetch_feed_disabled(self, mock_config_manager):
        """Test fetching a disabled feed."""
        mock_feed = Mock()
        mock_feed.enabled = False
        mock_config_manager.get_feed.return_value = mock_feed

        service = RSSFeedService()
        result = service.fetch_feed("disabled_feed")

        assert result is None


class TestNewsAnalyzer:
    """Test news analysis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = NewsAnalyzer()

    @patch("analytics.news_analyzer.RSSFeedService")
    def test_analyze_trending_topics_empty(self, mock_service):
        """Test trend analysis with no articles."""
        mock_service.return_value.get_all_recent_articles.return_value = []

        analyzer = NewsAnalyzer()
        trends = analyzer.analyze_trending_topics()

        assert trends == []

    @patch("analytics.news_analyzer.RSSFeedService")
    def test_suggest_timely_topics_empty(self, mock_service):
        """Test topic suggestions with no articles."""
        mock_service.return_value.get_all_recent_articles.return_value = []

        analyzer = NewsAnalyzer()
        suggestions = analyzer.suggest_timely_topics()

        assert suggestions == []

    def test_calculate_trend_score_empty(self):
        """Test trend score calculation with empty articles."""
        score = self.analyzer._calculate_trend_score([], 24)
        assert score == 0.0

    def test_suggest_topic_angle(self):
        """Test topic angle suggestions."""
        angle = self.analyzer._suggest_topic_angle("ai", [])
        assert "ai" in angle.lower()

        angle = self.analyzer._suggest_topic_angle("machine learning", [])
        assert "machine learning" in angle.lower()


class TestIntegration:
    """Integration tests for the MCP server."""

    @patch("utils.rss_utils.fetch_rss_feed")
    @patch("config.rss_config.RSSConfigManager")
    def test_full_workflow(self, mock_config_manager, mock_fetch):
        """Test a complete workflow from configuration to analysis."""
        # Mock configuration
        mock_feed = FeedConfig(
            id="test_feed",
            name="Test Feed",
            url="https://example.com/feed.xml",
            type="standard_rss",
            keywords=["test", "news"],
            enabled=True,
        )

        mock_config_manager.return_value.get_feed.return_value = mock_feed
        mock_config_manager.return_value.get_enabled_feeds.return_value = [mock_feed]

        # Mock feed data
        mock_feed_data = Mock()
        mock_feed_data.feed.title = "Test Feed"
        mock_feed_data.entries = [
            Mock(
                title="Test Article",
                description="Test description with news content",
                link="https://example.com/article",
                published="2024-01-01T00:00:00Z",
                id="test-article-1",
            )
        ]
        mock_fetch.return_value = mock_feed_data

        # Test the service
        service = RSSFeedService()
        feed_data = service.fetch_feed("test_feed")

        assert feed_data is not None
        assert feed_data.feed_id == "test_feed"
        assert len(feed_data.articles) == 1


if __name__ == "__main__":
    pytest.main([__file__])
