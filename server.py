"""
RSS News Analyzer MCP Server

This MCP server provides tools for RSS news analysis and trend detection.
"""

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv, find_dotenv
from src.tools.rss_tools import register_rss_tools

# Load environment variables
load_dotenv(find_dotenv())

# Create FastMCP server instance
mcp = FastMCP()

register_rss_tools(mcp)


def main():
    """Main entry point for the RSS News Analyzer MCP Server."""
    mcp.run()


if __name__ == "__main__":
    main()
