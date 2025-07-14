"""
RSS feed parsing utility functions for news processing.
"""

import re
import feedparser
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import unquote
import html


def fetch_rss_feed(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetches and parses an RSS feed from the specified URL.

    Args:
        url (str): The URL of the RSS feed to fetch

    Returns:
        Optional[Dict[str, Any]]: Parsed RSS feed data or None if error
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/58.0.3029.110 Safari/537.3"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if feed.bozo:
            print(f"Warning: RSS feed may be malformed: "
                  f"{feed.bozo_exception}")

        return feed
    except requests.exceptions.RequestException as e:
        print(f"Error fetching RSS feed from {url}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing RSS feed from {url}: {e}")
        return None


def extract_feed_metadata(feed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts metadata from an RSS feed.

    Args:
        feed (Dict[str, Any]): Parsed RSS feed data

    Returns:
        Dict[str, Any]: Feed metadata including title, description, etc.
    """
    if not feed or not hasattr(feed, 'feed'):
        return {}

    metadata = {
        'title': getattr(feed.feed, 'title', ''),
        'description': getattr(feed.feed, 'description', ''),
        'language': getattr(feed.feed, 'language', ''),
        'link': getattr(feed.feed, 'link', ''),
        'image': getattr(feed.feed, 'image', {}),
        'updated': getattr(feed.feed, 'updated', ''),
        'author': getattr(feed.feed, 'author', ''),
        'copyright': getattr(feed.feed, 'copyright', ''),
        'total_articles': len(getattr(feed, 'entries', []))
    }

    return metadata


def parse_google_alerts_feed(feed_url: str) -> Optional[Dict[str, Any]]:
    """
    Parse Google Alerts RSS feed with specific handling for alerts format.
    
    Args:
        feed_url (str): URL of the Google Alerts RSS feed
        
    Returns:
        Optional[Dict[str, Any]]: Parsed Google Alerts data
    """
    feed = fetch_rss_feed(feed_url)
    if not feed:
        return None
        
    metadata = extract_feed_metadata(feed)
    articles = extract_google_alerts_articles(feed)
    
    return {
        'metadata': metadata,
        'articles': articles,
        'feed_url': feed_url,
        'feed_type': 'google_alerts',
        'last_updated': datetime.now().isoformat()
    }


def extract_google_alerts_articles(feed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract articles from Google Alerts RSS feed.
    
    Args:
        feed (Dict[str, Any]): Parsed RSS feed data
        
    Returns:
        List[Dict[str, Any]]: List of news articles
    """
    if not feed or not hasattr(feed, 'entries'):
        return []
        
    articles = []
    
    for entry in feed.entries:
        article = {
            'id': getattr(entry, 'id', '') or getattr(entry, 'link', ''),
            'title': clean_google_alerts_title(getattr(entry, 'title', '')),
            'description': clean_google_alerts_description(getattr(entry, 'description', '')),
            'summary': clean_google_alerts_description(getattr(entry, 'summary', '')),
            'published': getattr(entry, 'published', ''),
            'published_parsed': getattr(entry, 'published_parsed', None),
            'link': extract_google_alerts_link(getattr(entry, 'link', '')),
            'source': extract_google_alerts_source(getattr(entry, 'title', '')),
            'alert_query': extract_google_alerts_query(feed),
            'raw_link': getattr(entry, 'link', ''),
            'raw_title': getattr(entry, 'title', ''),
            'raw_description': getattr(entry, 'description', '')
        }
        
        # Extract additional metadata
        if hasattr(entry, 'author'):
            article['author'] = entry.author
            
        articles.append(article)
        
    return articles


def clean_google_alerts_title(title: str) -> str:
    """
    Clean Google Alerts title by removing source prefix.
    
    Args:
        title (str): Raw title from Google Alerts
        
    Returns:
        str: Cleaned title
    """
    if not title:
        return ''
        
    # Google Alerts titles often have format "Article Title - Source"
    # Remove the source part
    parts = title.split(' - ')
    if len(parts) > 1:
        # Return everything except the last part (which is usually the source)
        return ' - '.join(parts[:-1]).strip()
    
    return title.strip()


def clean_google_alerts_description(description: str) -> str:
    """
    Clean Google Alerts description by removing HTML and Google-specific content.
    
    Args:
        description (str): Raw description from Google Alerts
        
    Returns:
        str: Cleaned description
    """
    if not description:
        return ''
        
    # Remove HTML tags
    description = re.sub(r'<[^>]+>', '', description)
    
    # Decode HTML entities
    description = html.unescape(description)
    
    # Remove Google-specific patterns
    description = re.sub(r'<b>.*?</b>', '', description)  # Remove bold tags
    description = re.sub(r'&nbsp;', ' ', description)      # Replace non-breaking spaces
    description = re.sub(r'\s+', ' ', description)         # Normalize whitespace
    
    return description.strip()


def extract_google_alerts_link(raw_link: str) -> str:
    """
    Extract the actual article URL from Google Alerts redirect link.
    
    Args:
        raw_link (str): Raw link from Google Alerts
        
    Returns:
        str: Actual article URL
    """
    if not raw_link:
        return ''
        
    # Google Alerts links are often redirect URLs
    # Format: https://www.google.com/url?rct=j&sa=t&url=ACTUAL_URL&...
    
    # Try to extract URL parameter
    url_match = re.search(r'[?&]url=([^&]+)', raw_link)
    if url_match:
        return unquote(url_match.group(1))
        
    # Try to extract q parameter (alternative format)
    q_match = re.search(r'[?&]q=([^&]+)', raw_link)
    if q_match:
        return unquote(q_match.group(1))
    
    # If no redirect pattern found, return original link
    return raw_link


def extract_google_alerts_source(title: str) -> str:
    """
    Extract the source/publisher from Google Alerts title.
    
    Args:
        title (str): Raw title from Google Alerts
        
    Returns:
        str: Source/publisher name
    """
    if not title:
        return ''
        
    # Google Alerts titles often have format "Article Title - Source"
    parts = title.split(' - ')
    if len(parts) > 1:
        return parts[-1].strip()  # Last part is usually the source
    
    return ''


def extract_google_alerts_query(feed: Dict[str, Any]) -> str:
    """
    Extract the search query from Google Alerts feed.
    
    Args:
        feed (Dict[str, Any]): Parsed RSS feed data
        
    Returns:
        str: Search query used for the alert
    """
    if not feed or not hasattr(feed, 'feed'):
        return ''
        
    # Try to extract from feed title
    feed_title = getattr(feed.feed, 'title', '')
    if feed_title:
        # Google Alerts feed titles often contain "Google Alert - QUERY"
        match = re.search(r'Google Alert - (.+)', feed_title)
        if match:
            return match.group(1).strip()
            
    # Try to extract from feed description
    feed_description = getattr(feed.feed, 'description', '')
    if feed_description:
        match = re.search(r'Google Alert - (.+)', feed_description)
        if match:
            return match.group(1).strip()
            
    return ''


def extract_news_keywords(text: str, predefined_keywords: List[str] = None) -> List[str]:
    """
    Extract relevant keywords from news article text.
    
    Args:
        text (str): Article text (title + description)
        predefined_keywords (List[str], optional): List of keywords to look for
        
    Returns:
        List[str]: List of found keywords
    """
    if not text:
        return []
        
    keywords = []
    text_lower = text.lower()
    
    # Use predefined keywords if provided
    if predefined_keywords:
        for keyword in predefined_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)
    
    # Common tech/AI keywords
    default_keywords = [
        'artificial intelligence', 'ai', 'machine learning', 'ml', 'deep learning',
        'agentic ai', 'agentic', 'ai agents', 'ai agent', 'autonomous ai', 'agent',
        'neural network', 'nlp', 'computer vision', 'data science', 'analytics',
        'big data', 'python', 'programming', 'algorithm', 'automation',
        'cloud computing', 'aws', 'azure', 'gcp', 'blockchain', 'cryptocurrency',
        'startup', 'venture capital', 'funding', 'ipo', 'acquisition',
        'cybersecurity', 'privacy', 'gdpr', 'regulation', 'policy'
    ]
    
    for keyword in default_keywords:
        if keyword in text_lower:
            keywords.append(keyword)
            
    return list(set(keywords))  # Remove duplicates


def extract_companies_from_text(text: str) -> List[str]:
    """
    Extract company names from news article text.
    
    Args:
        text (str): Article text
        
    Returns:
        List[str]: List of company names found
    """
    if not text:
        return []
        
    companies = []
    
    # Common tech companies
    tech_companies = [
        'Google', 'Apple', 'Microsoft', 'Amazon', 'Meta', 'Facebook',
        'Tesla', 'Netflix', 'Spotify', 'Uber', 'Airbnb', 'Twitter', 'X',
        'LinkedIn', 'Instagram', 'YouTube', 'OpenAI', 'Anthropic',
        'IBM', 'Oracle', 'Salesforce', 'Adobe', 'Nvidia', 'Intel',
        'AMD', 'Qualcomm', 'Samsung', 'Sony', 'Huawei', 'Xiaomi'
    ]
    
    for company in tech_companies:
        if company in text:
            companies.append(company)
            
    return list(set(companies))  # Remove duplicates


def is_google_alerts_feed(feed_url: str) -> bool:
    """
    Check if a URL is a Google Alerts RSS feed.
    
    Args:
        feed_url (str): RSS feed URL
        
    Returns:
        bool: True if it's a Google Alerts feed
    """
    return 'google.com/alerts/feeds' in feed_url


def normalize_news_date(date_str: str) -> str:
    """
    Normalize news article date to ISO format.
    
    Args:
        date_str (str): Date string in various formats
        
    Returns:
        str: ISO formatted date string
    """
    if not date_str:
        return ''
        
    try:
        # Try parsing common formats
        for fmt in ['%a, %d %b %Y %H:%M:%S %Z',
                   '%Y-%m-%dT%H:%M:%S%z',
                   '%Y-%m-%d %H:%M:%S',
                   '%d %b %Y %H:%M:%S']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
                
        # If no format works, return original
        return date_str
        
    except Exception:
        return date_str


def parse_standard_rss_feed(feed_url: str) -> Optional[Dict[str, Any]]:
    """
    Parse a standard RSS feed.
    
    Args:
        feed_url (str): URL of the RSS feed
        
    Returns:
        Optional[Dict[str, Any]]: Parsed RSS data
    """
    feed = fetch_rss_feed(feed_url)
    if not feed:
        return None
        
    metadata = extract_feed_metadata(feed)
    articles = extract_standard_rss_articles(feed)
    
    return {
        'metadata': metadata,
        'articles': articles,
        'feed_url': feed_url,
        'feed_type': 'standard_rss',
        'last_updated': datetime.now().isoformat()
    }


def extract_standard_rss_articles(feed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract articles from standard RSS feed.
    
    Args:
        feed (Dict[str, Any]): Parsed RSS feed data
        
    Returns:
        List[Dict[str, Any]]: List of news articles
    """
    if not feed or not hasattr(feed, 'entries'):
        return []
        
    articles = []
    
    for entry in feed.entries:
        article = {
            'id': getattr(entry, 'id', '') or getattr(entry, 'link', ''),
            'title': getattr(entry, 'title', ''),
            'description': getattr(entry, 'description', ''),
            'summary': getattr(entry, 'summary', ''),
            'published': getattr(entry, 'published', ''),
            'published_parsed': getattr(entry, 'published_parsed', None),
            'link': getattr(entry, 'link', ''),
            'source': extract_feed_metadata(feed).get('title', ''),
            'author': getattr(entry, 'author', ''),
            'tags': getattr(entry, 'tags', []),
            'category': getattr(entry, 'category', ''),
            'raw_title': getattr(entry, 'title', ''),
            'raw_description': getattr(entry, 'description', '')
        }
        
        articles.append(article)
        
    return articles