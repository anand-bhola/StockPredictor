"""
News fetcher module for Stock Predictor.
Fetches financial news from RSS feeds and web scraping.
"""

import logging
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetches financial news from multiple sources."""

    def __init__(self, config: Dict):
        """
        Initialize NewsFetcher.

        Args:
            config: Configuration dictionary with news settings
        """
        self.config = config
        self.rss_feeds = config.get('rss_feeds', [])
        self.scrape_sources = config.get('scrape_sources', [])
        self.max_age_hours = config.get('max_article_age_hours', 24)
        self.max_articles = config.get('articles_per_cycle', 50)

    def fetch_news(self, stock_symbols: List[str] = None) -> List[Dict]:
        """
        Fetch news from all sources.

        Args:
            stock_symbols: List of stock symbols to filter by (None = all news)

        Returns:
            List of news articles with metadata
        """
        articles = []

        # Fetch from RSS feeds
        for feed_config in self.rss_feeds:
            try:
                feed_articles = self._fetch_rss_feed(feed_config)
                articles.extend(feed_articles)
                logger.info(f"Fetched {len(feed_articles)} articles from {feed_config['name']}")
            except Exception as e:
                logger.warning(f"Error fetching RSS feed {feed_config['name']}: {e}")

        # Filter by age
        articles = self._filter_by_age(articles)

        # Filter by stock symbols if provided
        if stock_symbols:
            articles = self._filter_by_symbols(articles, stock_symbols)

        # Deduplicate
        articles = self._deduplicate_articles(articles)

        # Limit to max articles
        articles = articles[:self.max_articles]

        logger.info(f"Total articles fetched: {len(articles)}")
        return articles

    def _fetch_rss_feed(self, feed_config: Dict) -> List[Dict]:
        """Fetch articles from an RSS feed."""
        articles = []
        url = feed_config['url']
        name = feed_config['name']

        try:
            feed = feedparser.parse(url)

            if feed.bozo:
                logger.warning(f"RSS feed {name} returned malformed XML")

            for entry in feed.entries:
                try:
                    article = {
                        'title': entry.get('title', 'Unknown'),
                        'summary': entry.get('summary', ''),
                        'content': entry.get('content', [{}])[0].get('value', '') if entry.get('content') else '',
                        'source': name,
                        'url': entry.get('link', ''),
                        'published_at': self._parse_date(entry.get('published')),
                    }
                    articles.append(article)
                except Exception as e:
                    logger.debug(f"Error parsing RSS entry from {name}: {e}")

            return articles
        except Exception as e:
            logger.error(f"Error fetching RSS feed {name}: {e}")
            return []

    def _filter_by_age(self, articles: List[Dict]) -> List[Dict]:
        """Filter articles older than max_age_hours."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
        filtered = []

        for article in articles:
            pub_date = article.get('published_at')
            if pub_date and pub_date > cutoff_time:
                filtered.append(article)
            elif not pub_date:
                # Include articles without dates
                filtered.append(article)

        return filtered

    def _filter_by_symbols(self, articles: List[Dict], symbols: List[str]) -> List[Dict]:
        """Filter articles that mention stock symbols or market keywords."""
        filtered = []
        symbols_upper = [s.upper() for s in symbols]

        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('summary', '')).upper()

            # Check for exact symbol matches
            if any(symbol in text for symbol in symbols_upper):
                filtered.append(article)
            # Check for market keywords
            elif any(keyword in text for keyword in ['MARKET', 'STOCK', 'TRADING', 'EARNINGS']):
                filtered.append(article)

        return filtered

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title."""
        seen_titles = set()
        unique = []

        for article in articles:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                unique.append(article)
                seen_titles.add(title)

        return unique

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        # Try common date formats
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.replace('GMT', '+0000'), fmt)
            except ValueError:
                continue

        # Fallback to current time if parsing fails
        logger.debug(f"Could not parse date: {date_str}")
        return datetime.now()

    def fetch_yahoo_finance_news(self, stock_symbol: str) -> List[Dict]:
        """
        Fetch stock-specific news from Yahoo Finance (web scrape).

        Args:
            stock_symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            List of news articles
        """
        articles = []
        url = f"https://finance.yahoo.com/quote/{stock_symbol}/news"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Yahoo Finance news articles are typically in h3 tags with specific classes
            news_items = soup.find_all('h3', limit=10)

            for item in news_items:
                try:
                    link_elem = item.find('a')
                    if link_elem:
                        title = link_elem.get_text(strip=True)
                        href = link_elem.get('href', '')

                        # Make absolute URL if relative
                        if href.startswith('/'):
                            href = urljoin('https://finance.yahoo.com', href)

                        article = {
                            'title': title,
                            'summary': '',
                            'content': '',
                            'source': 'Yahoo Finance',
                            'url': href,
                            'published_at': datetime.now(),
                        }
                        articles.append(article)
                except Exception as e:
                    logger.debug(f"Error parsing Yahoo Finance news item: {e}")

            logger.info(f"Fetched {len(articles)} articles for {stock_symbol} from Yahoo Finance")
            return articles

        except requests.RequestException as e:
            logger.warning(f"Error fetching Yahoo Finance news for {stock_symbol}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in fetch_yahoo_finance_news: {e}")
            return []

    def extract_article_summary(self, article: Dict) -> str:
        """Extract a clean summary from article content."""
        summary = article.get('summary', '')
        if not summary:
            summary = article.get('content', '')

        # Remove HTML tags
        summary = re.sub('<[^<]+?>', '', summary)

        # Limit to first 500 characters
        summary = summary[:500].rstrip()

        return summary
