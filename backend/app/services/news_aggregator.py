import asyncio
import feedparser
import aiohttp
import ssl
import certifi
from datetime import datetime, timedelta
from typing import List, Optional
from bs4 import BeautifulSoup
import re

from app.core.config import settings
from app.models.schemas import NewsArticle


# Default news sources
SEA_TELEGRAM_CHANNELS = [
    "@channelnewsasia",
    "@malaymail",
    "@theikirei",
    "@sgreddit",
    "@techinasiasg",
]

SEA_RSS_FEEDS = {
    # Singapore
    "CNA": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
    "Straits Times": "https://www.straitstimes.com/news/asia/rss.xml",
    # Malaysia
    "Malay Mail": "https://www.malaymail.com/feed/rss/malaysia",
    "The Star": "https://www.thestar.com.my/rss/News/Nation",
    # Regional
    "SCMP SEA": "https://www.scmp.com/rss/91/feed",
    "Nikkei Asia": "https://asia.nikkei.com/rss/feed/nar",
    # AI/Tech
    "TechInAsia": "https://www.techinasia.com/feed",
    "e27": "https://e27.co/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
}

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]

TWITTER_ACCOUNTS = [
    "TechInAsia",
    "e27co",
    "CNABusiness",
    "NikkeiAsia",
]


class NewsAggregatorService:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        # Create SSL context with certifi certificates
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def aggregate_all(self, days: int = 7) -> List[NewsArticle]:
        """Aggregate news from all sources."""
        tasks = [
            self.fetch_rss_feeds(days),
            self.fetch_nitter_feeds(days),
        ]

        # Telegram requires separate handling due to auth
        # tasks.append(self.fetch_telegram_channels(days))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Error aggregating: {result}")

        return articles

    async def fetch_rss_feeds(self, days: int = 7) -> List[NewsArticle]:
        """Fetch articles from RSS feeds."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        session = await self._get_session()

        tasks = [
            self._fetch_single_rss_feed(session, source_name, feed_url, cutoff)
            for source_name, feed_url in SEA_RSS_FEEDS.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Error in RSS fetch task: {result}")

        return articles

    def _process_rss_content(
        self,
        content: str,
        source_name: str,
        cutoff: datetime
    ) -> List[NewsArticle]:
        """Process RSS content in a separate thread."""
        articles = []
        feed = feedparser.parse(content)

        for entry in feed.entries[:30]:
            published = self._parse_date(entry.get("published"))
            if published and published < cutoff:
                continue

            # Clean HTML from content
            content_raw = entry.get("summary", "") or entry.get("description", "")
            content_clean = self._clean_html(content_raw)

            articles.append(NewsArticle(
                source_type="rss",
                source_name=source_name,
                title=entry.get("title", ""),
                content=content_clean,
                url=entry.get("link", ""),
                published_at=published or datetime.utcnow(),
            ))
        return articles

    async def _fetch_single_rss_feed(
        self,
        session: aiohttp.ClientSession,
        source_name: str,
        feed_url: str,
        cutoff: datetime
    ) -> List[NewsArticle]:
        """Fetch and parse a single RSS feed."""
        try:
            async with session.get(feed_url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Offload CPU-bound parsing to a thread
                    return await asyncio.to_thread(
                        self._process_rss_content, content, source_name, cutoff
                    )
        except Exception as e:
            print(f"Error fetching RSS {source_name}: {e}")

        return []

    async def fetch_nitter_feeds(self, days: int = 7) -> List[NewsArticle]:
        """Fetch tweets via Nitter RSS (free Twitter alternative)."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        session = await self._get_session()

        tasks = [
            self._fetch_single_twitter_user(session, username, cutoff)
            for username in TWITTER_ACCOUNTS
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Error in Nitter fetch task: {result}")

        return articles

    def _process_nitter_content(
        self,
        content: str,
        username: str,
        cutoff: datetime
    ) -> List[NewsArticle]:
        """Process Nitter content in a separate thread."""
        articles = []
        feed = feedparser.parse(content)

        for entry in feed.entries[:20]:
            published = self._parse_date(entry.get("published"))
            if published and published < cutoff:
                continue

            content_clean = self._clean_html(entry.get("title", ""))

            articles.append(NewsArticle(
                source_type="nitter",
                source_name=f"@{username}",
                title=None,
                content=content_clean,
                url=entry.get("link", ""),
                published_at=published or datetime.utcnow(),
            ))
        return articles

    async def _fetch_single_twitter_user(
        self,
        session: aiohttp.ClientSession,
        username: str,
        cutoff: datetime
    ) -> List[NewsArticle]:
        """Fetch tweets for a single user with fallback."""
        for nitter_instance in NITTER_INSTANCES:
            try:
                url = f"{nitter_instance}/{username}/rss"
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Offload CPU-bound parsing to a thread
                        return await asyncio.to_thread(
                            self._process_nitter_content, content, username, cutoff
                        )
            except Exception:
                continue  # Try next Nitter instance

        return []

    async def fetch_telegram_channels(self, days: int = 7) -> List[NewsArticle]:
        """Fetch messages from Telegram channels."""
        articles = []

        # Only attempt if credentials are configured
        if not settings.telegram_api_id or not settings.telegram_api_hash:
            return articles

        try:
            from telethon import TelegramClient

            cutoff = datetime.utcnow() - timedelta(days=days)

            async with TelegramClient(
                settings.telegram_session_name,
                settings.telegram_api_id,
                settings.telegram_api_hash
            ) as client:
                for channel in SEA_TELEGRAM_CHANNELS:
                    try:
                        async for message in client.iter_messages(channel, limit=100):
                            if message.date.replace(tzinfo=None) < cutoff:
                                break
                            if message.text:
                                articles.append(NewsArticle(
                                    source_type="telegram",
                                    source_name=channel,
                                    title=None,
                                    content=message.text,
                                    url=None,
                                    published_at=message.date.replace(tzinfo=None),
                                ))
                    except Exception as e:
                        print(f"Error fetching Telegram {channel}: {e}")
                        continue
        except ImportError:
            print("Telethon not installed, skipping Telegram")
        except Exception as e:
            print(f"Telegram error: {e}")

        return articles

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from various formats."""
        if not date_str:
            return None

        from dateutil import parser
        try:
            dt = parser.parse(date_str)
            # Remove timezone info for consistency
            return dt.replace(tzinfo=None)
        except Exception:
            return None

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and clean text."""
        if not html:
            return ""

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(separator=" ")

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text


# Singleton instance
_aggregator: Optional[NewsAggregatorService] = None


def get_news_aggregator() -> NewsAggregatorService:
    global _aggregator
    if _aggregator is None:
        _aggregator = NewsAggregatorService()
    return _aggregator
