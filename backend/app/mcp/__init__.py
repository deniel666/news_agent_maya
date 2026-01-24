"""MCP (Model Context Protocol) integration for Maya AI News Anchor.

This module provides:
- MCP server configuration and management
- Client wrapper for MCP tool calls
- Registry for server lifecycle management
- Default configurations for trending, news, images, and analytics MCPs
"""

from .config import MCPServerConfig, AgentMCPConfig, MCPToolConfig
from .registry import MCPRegistry, get_mcp_registry
from .client import MCPClient
from .defaults import (
    GOOGLE_NEWS_TRENDS,
    WHAT_HAPPEN,
    STOCKY,
    TRENDS_MCP,
    METRICOOL,
    VIRAL_APP,
    DEFAULT_MCP_SERVERS,
)

__all__ = [
    # Config
    "MCPServerConfig",
    "AgentMCPConfig",
    "MCPToolConfig",
    # Registry
    "MCPRegistry",
    "get_mcp_registry",
    # Client
    "MCPClient",
    # Defaults
    "GOOGLE_NEWS_TRENDS",
    "WHAT_HAPPEN",
    "STOCKY",
    "TRENDS_MCP",
    "METRICOOL",
    "VIRAL_APP",
    "DEFAULT_MCP_SERVERS",
]
