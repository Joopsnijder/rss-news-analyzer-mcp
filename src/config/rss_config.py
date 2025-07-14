"""
RSS feed configuration management system.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeedConfig:
    """Configuration for a single RSS feed."""
    id: str
    name: str
    url: str
    type: str = "standard_rss"  # standard_rss, google_alerts, etc.
    keywords: List[str] = None
    update_frequency: str = "1h"  # 1h, 6h, 12h, 24h
    enabled: bool = True
    analysis_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.analysis_settings is None:
            self.analysis_settings = {}


class RSSConfigManager:
    """Manager for RSS feed configurations."""
    
    def __init__(self, config_file: str = "rss_feeds_config.json"):
        """
        Initialize RSS config manager.
        
        Args:
            config_file: Path to the RSS configuration file
        """
        self.config_file = config_file
        self.config_path = self._get_config_path()
        self.feeds = {}
        self.load_config()
    
    def _get_config_path(self) -> str:
        """Get the full path to the configuration file."""
        if os.path.isabs(self.config_file):
            return self.config_file
        
        # Place config file in project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(project_root, self.config_file)
    
    def load_config(self) -> None:
        """Load RSS feed configurations from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    
                # Load feeds
                for feed_data in config_data.get('feeds', []):
                    feed_config = FeedConfig(**feed_data)
                    self.feeds[feed_config.id] = feed_config
                    
                logger.info(f"Loaded {len(self.feeds)} RSS feed configurations")
            else:
                logger.info("No RSS config file found, creating default configuration")
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading RSS config: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create a default RSS configuration."""
        default_feeds = [
            FeedConfig(
                id="google_alerts_ai",
                name="Google Alerts - AI",
                url="https://www.google.com/alerts/feeds/01516800834195557068/15279974359414489902",
                type="google_alerts",
                keywords=["AI", "artificial intelligence", "machine learning"],
                update_frequency="1h",
                enabled=True,
                analysis_settings={
                    "track_sentiment": True,
                    "extract_companies": True,
                    "detect_trends": True
                }
            )
        ]
        
        for feed in default_feeds:
            self.feeds[feed.id] = feed
            
        self.save_config()
    
    def save_config(self) -> None:
        """Save RSS feed configurations to file."""
        try:
            config_data = {
                "feeds": [asdict(feed) for feed in self.feeds.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"Saved RSS config to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving RSS config: {e}")
            raise
    
    def add_feed(self, feed_config: FeedConfig) -> bool:
        """
        Add a new RSS feed configuration.
        
        Args:
            feed_config: Feed configuration to add
            
        Returns:
            bool: True if added successfully
        """
        try:
            if feed_config.id in self.feeds:
                logger.warning(f"Feed ID {feed_config.id} already exists")
                return False
                
            # Validate feed configuration
            if not self._validate_feed_config(feed_config):
                return False
                
            self.feeds[feed_config.id] = feed_config
            self.save_config()
            logger.info(f"Added RSS feed: {feed_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding RSS feed: {e}")
            return False
    
    def update_feed(self, feed_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing RSS feed configuration.
        
        Args:
            feed_id: ID of the feed to update
            updates: Dictionary of updates to apply
            
        Returns:
            bool: True if updated successfully
        """
        try:
            if feed_id not in self.feeds:
                logger.warning(f"Feed ID {feed_id} not found")
                return False
                
            feed = self.feeds[feed_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(feed, key):
                    setattr(feed, key, value)
                else:
                    logger.warning(f"Unknown feed attribute: {key}")
            
            # Validate updated configuration
            if not self._validate_feed_config(feed):
                return False
                
            self.save_config()
            logger.info(f"Updated RSS feed: {feed_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating RSS feed: {e}")
            return False
    
    def remove_feed(self, feed_id: str) -> bool:
        """
        Remove an RSS feed configuration.
        
        Args:
            feed_id: ID of the feed to remove
            
        Returns:
            bool: True if removed successfully
        """
        try:
            if feed_id not in self.feeds:
                logger.warning(f"Feed ID {feed_id} not found")
                return False
                
            del self.feeds[feed_id]
            self.save_config()
            logger.info(f"Removed RSS feed: {feed_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing RSS feed: {e}")
            return False
    
    def get_feed(self, feed_id: str) -> Optional[FeedConfig]:
        """
        Get a specific RSS feed configuration.
        
        Args:
            feed_id: ID of the feed to retrieve
            
        Returns:
            FeedConfig or None if not found
        """
        return self.feeds.get(feed_id)
    
    def get_all_feeds(self) -> List[FeedConfig]:
        """
        Get all RSS feed configurations.
        
        Returns:
            List of all feed configurations
        """
        return list(self.feeds.values())
    
    def get_enabled_feeds(self) -> List[FeedConfig]:
        """
        Get all enabled RSS feed configurations.
        
        Returns:
            List of enabled feed configurations
        """
        return [feed for feed in self.feeds.values() if feed.enabled]
    
    def get_feeds_by_type(self, feed_type: str) -> List[FeedConfig]:
        """
        Get RSS feeds by type.
        
        Args:
            feed_type: Type of feeds to retrieve
            
        Returns:
            List of feeds matching the type
        """
        return [feed for feed in self.feeds.values() if feed.type == feed_type]
    
    def _validate_feed_config(self, feed_config: FeedConfig) -> bool:
        """
        Validate RSS feed configuration.
        
        Args:
            feed_config: Feed configuration to validate
            
        Returns:
            bool: True if valid
        """
        try:
            # Check required fields
            if not feed_config.id:
                logger.error("Feed ID is required")
                return False
                
            if not feed_config.name:
                logger.error("Feed name is required")
                return False
                
            if not feed_config.url:
                logger.error("Feed URL is required")
                return False
            
            # Basic URL validation
            if not feed_config.url.startswith(('http://', 'https://')):
                logger.error("Feed URL must start with http:// or https://")
                return False
            
            # Validate update frequency
            valid_frequencies = ['1h', '6h', '12h', '24h']
            if feed_config.update_frequency not in valid_frequencies:
                logger.error(f"Invalid update frequency: {feed_config.update_frequency}")
                return False
            
            # Validate type
            valid_types = ['standard_rss', 'google_alerts', 'atom', 'custom']
            if feed_config.type not in valid_types:
                logger.error(f"Invalid feed type: {feed_config.type}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating feed config: {e}")
            return False
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.feeds = {}
        self.load_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current RSS configuration.
        
        Returns:
            Dictionary containing configuration summary
        """
        enabled_feeds = self.get_enabled_feeds()
        
        return {
            "total_feeds": len(self.feeds),
            "enabled_feeds": len(enabled_feeds),
            "disabled_feeds": len(self.feeds) - len(enabled_feeds),
            "feed_types": {
                feed_type: len(self.get_feeds_by_type(feed_type))
                for feed_type in set(feed.type for feed in self.feeds.values())
            },
            "config_file": self.config_path,
            "last_loaded": datetime.now().isoformat()
        }


# Global instance
rss_config_manager = RSSConfigManager()