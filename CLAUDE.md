# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an RSS News Analyzer MCP (Model Context Protocol) server that provides tools for monitoring RSS feeds, analyzing news trends, and detecting content spikes. The server is built using FastMCP and provides comprehensive news analysis capabilities.

## Key Commands

### Development and Testing
- `uv run mcp dev server.py` - Run in development mode
- `uv run server.py` - Run in production mode
- `uv run pytest tests/` - Run all tests
- `uv run pytest tests/test_server.py` - Run specific test file
- `uv sync` - Install/sync dependencies
- `npx @modelcontextprotocol/inspector uv run server.py` - Use MCP inspector for debugging

### Code Quality
- `flake8` - Check for linting errors (must be run before commits)

## Architecture

The codebase follows a modular architecture with clear separation of concerns:

```
src/
├── analytics/          # News analysis and trend detection
│   └── news_analyzer.py
├── config/            # RSS feed configuration management
│   └── rss_config.py
├── content/           # RSS feed processing and caching
│   └── rss_feed_service.py
├── tools/             # MCP tools registration and implementations
│   └── rss_tools.py
└── utils/             # Utility functions
    ├── cache_manager.py
    └── rss_utils.py
```

### Key Components

1. **FastMCP Server** (`server.py`): Main entry point that registers all RSS tools
2. **RSS Tools** (`src/tools/rss_tools.py`): MCP tool implementations for feed management and analysis
3. **RSS Feed Service** (`src/content/rss_feed_service.py`): Core service for fetching and processing RSS feeds
4. **News Analyzer** (`src/analytics/news_analyzer.py`): Trend detection, spike analysis, and topic suggestions
5. **RSS Config Manager** (`src/config/rss_config.py`): Manages RSS feed configuration from JSON
6. **Cache Manager** (`src/utils/cache_manager.py`): TTL-based caching system for performance
7. **RSS Utils** (`src/utils/rss_utils.py`): Feed parsing utilities with Google Alerts support

## Configuration

- **RSS Feeds**: Configure in `rss_feeds_config.json` (root directory)
- **Environment Variables**: Optional `.env` file for API keys and settings
- **Feed Types**: Supports standard RSS, Atom, Google Alerts, and custom formats
- **Caching**: 1-hour TTL by default, configurable via environment variables

## Key Features

- RSS feed management and monitoring
- Google Alerts specialized parsing
- Trend analysis and spike detection
- Company mention tracking
- Keyword extraction and analysis
- Comprehensive debugging tools
- Intelligent caching with TTL support

## Development Notes

- Uses `uv` for dependency management
- Python 3.13+ required
- All MCP tools are registered in `src/tools/rss_tools.py`
- The server uses FastMCP for simplified MCP server creation
- Comprehensive error handling and logging throughout
- Cache files are stored in project root and auto-invalidated
