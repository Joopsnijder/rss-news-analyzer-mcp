# RSS News Analyzer MCP Server

A Model Context Protocol (MCP) server for RSS news analysis and trend detection. This server provides tools for monitoring RSS feeds, analyzing news trends, detecting content spikes, and generating insights from news articles.

## Features

- **RSS Feed Management**: Configure and monitor multiple RSS feeds
- **Google Alerts Support**: Specialized parsing for Google Alerts RSS feeds
- **Trend Analysis**: Detect trending topics and keywords from news articles
- **Spike Detection**: Identify sudden increases in topic coverage
- **Company Mentions**: Track mentions of companies in news articles
- **Keyword Analysis**: Extract and analyze relevant keywords from articles
- **Caching**: Efficient caching system with TTL support
- **Debugging Tools**: Comprehensive debugging and analysis tools

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rss-news-analyzer-mcp
```

2. Install dependencies:
```bash
uv sync
```

3. Configure RSS feeds by editing `rss_feeds_config.json`

4. Optional: Set up environment variables by copying `.env.example` to `.env`

## Configuration

### RSS Feeds Configuration

Edit `rss_feeds_config.json` to configure your RSS feeds:

```json
{
  "feeds": [
    {
      "id": "google_alerts_ai",
      "name": "Google Alerts - AI",
      "url": "https://www.google.com/alerts/feeds/YOUR_FEED_ID/YOUR_FEED_TOKEN",
      "type": "google_alerts",
      "keywords": ["AI", "artificial intelligence", "machine learning"],
      "update_frequency": "1h",
      "enabled": true,
      "analysis_settings": {
        "track_sentiment": true,
        "extract_companies": true,
        "detect_trends": true
      }
    }
  ]
}
```

### Feed Types

- **google_alerts**: Google Alerts RSS feeds with specialized parsing
- **standard_rss**: Standard RSS/Atom feeds
- **atom**: Atom feeds
- **custom**: Custom feed formats

### Environment Variables

Optional environment variables (create `.env` file):

```bash
# OpenAI API (optional - for advanced analysis)
OPENAI_API_KEY=your_api_key
OPENAI_ORGANIZATION_ID=your_org_id

# Logging
LOG_LEVEL=INFO

# Cache settings
CACHE_TTL_HOURS=1
```

## Running the Server

### Development Mode

```bash
uv run mcp dev server.py
```

### Production Mode

```bash
uv run server.py
```

### Using MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run server.py
```

## Available Tools

### Feed Management

- `configure_rss_feeds()`: Get configuration and management instructions
- `get_rss_feeds(enabled_only=True)`: List configured feeds
- `fetch_rss_feed(feed_id, force_refresh=False)`: Fetch specific feed
- `refresh_all_feeds()`: Refresh all enabled feeds
- `get_feed_statistics(feed_id=None)`: Get feed statistics

### News Analysis

- `analyze_news_trends(hours=24, min_mentions=3)`: Analyze trending topics
- `get_trending_keywords(hours=24)`: Get trending keywords
- `detect_news_spikes(hours=24, comparison_hours=168)`: Detect coverage spikes
- `get_news_summary(hours=24)`: Get comprehensive news summary
- `suggest_timely_topics(hours=24)`: Suggest timely topics for content creation

### Search and Discovery

- `search_news_articles(query, feed_id=None, hours=168)`: Search articles
- `get_company_mentions(hours=24)`: Analyze company mentions

### Debugging

- `debug_rss_feed(feed_id)`: Debug feed connectivity and parsing
- `analyze_feed_keywords(feed_id, hours=168)`: Analyze keyword matching
- `get_all_feed_articles(feed_id, limit=20)`: Get all articles from feed

## Usage Examples

### Basic Trend Analysis

```python
# Get trending topics from last 24 hours
trends = analyze_news_trends(hours=24, min_mentions=3)
```

### Company Monitoring

```python
# Track company mentions in recent news
companies = get_company_mentions(hours=24)
```

### Content Suggestions

```python
# Get timely topic suggestions
suggestions = suggest_timely_topics(hours=24)
```

### Feed Debugging

```python
# Debug feed issues
debug_info = debug_rss_feed("google_alerts_ai")
```

## Google Alerts Setup

1. Create a Google Alert at [google.com/alerts](https://www.google.com/alerts)
2. Set delivery to "RSS feed"
3. Copy the RSS feed URL
4. Add to your `rss_feeds_config.json` with type "google_alerts"

## Architecture

```
src/
├── analytics/          # News analysis and trend detection
│   └── news_analyzer.py
├── config/            # RSS feed configuration management
│   └── rss_config.py
├── content/           # RSS feed processing
│   └── rss_feed_service.py
├── tools/             # MCP tools registration
│   └── rss_tools.py
└── utils/             # Utility functions
    ├── cache_manager.py
    └── rss_utils.py
```

## Key Components

- **News Analyzer**: Trend detection, spike analysis, topic suggestions
- **RSS Feed Service**: Feed processing, caching, article extraction
- **RSS Config Manager**: Feed configuration and management
- **RSS Utils**: Feed parsing, Google Alerts support, keyword extraction
- **Cache Manager**: TTL-based caching for performance

## Caching

The server uses an intelligent caching system:
- Feed data cached for 1 hour (configurable)
- Cache files stored in project root
- Automatic cache invalidation based on TTL
- Force refresh option available

## Error Handling

- Comprehensive error handling for feed failures
- Graceful degradation when feeds are unavailable
- Detailed debug information for troubleshooting
- Logging for monitoring and debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Testing

Run the test suite:

```bash
uv run pytest tests/
```

Run specific test file:

```bash
uv run pytest tests/test_server.py
```

## License

[Add your license information here]

## Support

For issues and questions:
- Check the debug tools (`debug_rss_feed`, `analyze_feed_keywords`)
- Review the logs for error messages
- Verify RSS feed URLs are accessible
- Check configuration format in `rss_feeds_config.json`

## Changelog

### v0.1.0
- Initial release
- RSS feed management and analysis
- Google Alerts support
- Trend detection and spike analysis
- Company mention tracking
- Comprehensive debugging tools