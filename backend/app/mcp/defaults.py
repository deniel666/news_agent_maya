"""Default MCP server configurations for Maya AI News Anchor.

This module provides pre-configured MCP servers for:
1. Trending/Hyped content discovery (Google Trends, Trends-MCP)
2. News sources (What Happen)
3. Stock images (Stocky)
4. SMM Analytics (Metricool, viral.app)
"""

from .config import MCPServerConfig, MCPTransportType


# =============================================================================
# 1. TRENDING & HYPED CONTENT DISCOVERY
# =============================================================================

GOOGLE_NEWS_TRENDS = MCPServerConfig(
    id="google_trends",
    name="Google News & Trends",
    description="Get trending topics and news by country, including Malaysia",
    transport=MCPTransportType.STDIO,
    command="uvx",
    args=["google-news-trends-mcp@latest"],
    tools=[
        "get_trending_keywords",
        "get_news_by_keyword",
        "get_news_by_location",
        "get_news_by_topic",
    ],
    cost_per_call=0.0,  # FREE
)

TRENDS_MCP = MCPServerConfig(
    id="trends_mcp",
    name="Trends MCP (YouTube, TikTok, Instagram)",
    description="Fetch trending videos across platforms by region",
    transport=MCPTransportType.STDIO,
    command="uv",
    args=[
        "run", "--with", "mcp[cli]", "--with", "fastmcp",
        "--with", "yt_dlp", "--with", "beautifulsoup4",
        "mcp", "run", "server.py"
    ],
    env={
        "tiktok": "${RAPIDAPI_KEY}",  # Optional for TikTok
    },
    tools=[
        "get_youtube_trending",
        "get_tiktok_trending",
        "get_instagram_reels_trends",
    ],
    enabled=False,  # Enable when RapidAPI key is available
    cost_per_call=0.01,  # ~$10/mo for TikTok API
)


# =============================================================================
# 2. NEWS SOURCES & FACTS
# =============================================================================

WHAT_HAPPEN = MCPServerConfig(
    id="what_happen",
    name="What Happen News",
    description="News aggregation from 70+ platforms including Southeast Asian sources",
    transport=MCPTransportType.STDIO,
    command="npx",
    args=["-y", "@anthropic/mcp-server-everything"],  # Placeholder - actual package may differ
    tools=["get_news"],
    cost_per_call=0.0,  # FREE
    enabled=False,  # Enable when package name is confirmed
)

RSS_NEWS_ANALYZER = MCPServerConfig(
    id="rss_analyzer",
    name="RSS News Analyzer",
    description="31 data sources with trend detection and spike analysis",
    transport=MCPTransportType.STDIO,
    command="python",
    args=["rss_news_analyzer_mcp.py"],
    tools=[
        "analyze_trends",
        "detect_spikes",
        "get_keywords",
    ],
    cost_per_call=0.0,  # FREE (needs OpenAI for analysis)
    enabled=False,  # Enable when set up locally
)


# =============================================================================
# 3. STOCK IMAGES
# =============================================================================

STOCKY = MCPServerConfig(
    id="stocky",
    name="Stocky Stock Images",
    description="Search Pexels + Unsplash simultaneously for stock images",
    transport=MCPTransportType.STDIO,
    command="python",
    args=["stocky_mcp.py"],
    env={
        "PEXELS_API_KEY": "${PEXELS_API_KEY}",
        "UNSPLASH_ACCESS_KEY": "${UNSPLASH_ACCESS_KEY}",
    },
    tools=[
        "search_stock_images",
        "get_image_details",
        "download_image",
    ],
    cost_per_call=0.0,  # FREE
    enabled=False,  # Enable when API keys are set
)

STOCK_IMAGES_MCP = MCPServerConfig(
    id="stock_images",
    name="Stock Images MCP (3 platforms)",
    description="Search Pexels, Unsplash, and Pixabay",
    transport=MCPTransportType.STDIO,
    command="uvx",
    args=["git+https://github.com/Zulelee/stock-images-mcp"],
    env={
        "UNSPLASH_API_KEY": "${UNSPLASH_ACCESS_KEY}",
        "PEXELS_API_KEY": "${PEXELS_API_KEY}",
        "PIXABAY_API_KEY": "${PIXABAY_API_KEY}",
    },
    tools=["search_images"],
    cost_per_call=0.0,
    enabled=False,
)


# =============================================================================
# 4. SMM ANALYTICS
# =============================================================================

METRICOOL = MCPServerConfig(
    id="metricool",
    name="Metricool Analytics",
    description="Full analytics + competitor tracking + best posting times",
    transport=MCPTransportType.STDIO,
    command="uvx",
    args=["--upgrade", "mcp-metricool"],
    env={
        "METRICOOL_USER_TOKEN": "${METRICOOL_USER_TOKEN}",
        "METRICOOL_USER_ID": "${METRICOOL_USER_ID}",
    },
    tools=[
        "get_analytics",
        "get_competitors",
        "get_best_time_to_post",
        "get_instagram_reels",
        "get_tiktok_videos",
    ],
    cost_per_call=0.0,  # Included in Metricool subscription
    enabled=False,  # Enable when Metricool subscription is active
)

VIRAL_APP = MCPServerConfig(
    id="viral_app",
    name="viral.app TikTok Analytics",
    description="Deep TikTok analytics with video performance and transcripts",
    transport=MCPTransportType.STDIO,
    command="npx",
    args=["-y", "mcp-remote@latest", "https://viral.app/api/mcp"],
    tools=[
        "get-tiktok-profile",
        "get-tiktok-video",
        "list-profile-videos",
    ],
    cost_per_call=0.05,  # ~20 free credits/month
    enabled=False,  # Enable when needed
)

SOCIAVAULT = MCPServerConfig(
    id="sociavault",
    name="SociaVault Multi-platform Analytics",
    description="Analytics across Instagram, TikTok, Twitter/X, Threads, YouTube, Facebook, Reddit",
    transport=MCPTransportType.STDIO,
    command="node",
    args=["dist/index.js"],
    env={
        "SOCIAVAULT_API_KEY": "${SOCIAVAULT_API_KEY}",
    },
    tools=[
        "get_profile",
        "get_posts",
        "get_engagement",
    ],
    cost_per_call=0.0,
    enabled=False,
)


# =============================================================================
# DEFAULT SERVERS LIST
# =============================================================================

DEFAULT_MCP_SERVERS = [
    # Week 1: Core Research (FREE)
    GOOGLE_NEWS_TRENDS,  # Primary - Malaysia trending
    STOCKY,              # Stock images

    # Week 2: Enhanced Research
    WHAT_HAPPEN,         # 70+ news sources
    TRENDS_MCP,          # Platform trends
    RSS_NEWS_ANALYZER,   # Trend detection
    STOCK_IMAGES_MCP,    # Alternative stock images

    # Month 2: Analytics
    METRICOOL,           # SMM analytics
    VIRAL_APP,           # TikTok deep analytics
    SOCIAVAULT,          # Multi-platform metrics
]


def get_free_servers() -> list:
    """Get only free MCP servers (no API costs)."""
    return [
        GOOGLE_NEWS_TRENDS,
        WHAT_HAPPEN,
        STOCKY,
        RSS_NEWS_ANALYZER,
    ]


def get_analytics_servers() -> list:
    """Get analytics-focused MCP servers."""
    return [
        METRICOOL,
        VIRAL_APP,
        SOCIAVAULT,
    ]
