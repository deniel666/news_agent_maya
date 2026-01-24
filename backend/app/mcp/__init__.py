"""MCP (Model Context Protocol) integration for Maya AI News Anchor.

This module provides:
- MCP server configuration and management
- Client wrapper for MCP tool calls (MCPClient + ComposioClient)
- Registry for server lifecycle management
- Default configurations for trending, news, images, and analytics MCPs

Supports two modes:
1. Composio Mode (preferred): Uses Composio Tool Router for 500+ tools
2. Legacy Mode: Uses individual MCP servers via stdio
"""

from .config import MCPServerConfig, AgentMCPConfig, MCPToolConfig
from .registry import MCPRegistry, get_mcp_registry
from .client import MCPClient
from .composio_client import ComposioClient, get_composio_client, init_composio_client
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
    # Clients
    "MCPClient",
    "ComposioClient",
    "get_composio_client",
    "init_composio_client",
    # Defaults
    "GOOGLE_NEWS_TRENDS",
    "WHAT_HAPPEN",
    "STOCKY",
    "TRENDS_MCP",
    "METRICOOL",
    "VIRAL_APP",
    "DEFAULT_MCP_SERVERS",
]
