"""MCP configuration models for Maya AI News Anchor.

This module defines:
- MCPServerConfig: Configuration for individual MCP servers
- AgentMCPConfig: MCP configuration for agents
- MCPToolConfig: Configuration for specific MCP tools
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from enum import Enum


class MCPTransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"      # Local subprocess via stdio
    SSE = "sse"          # Server-Sent Events (remote)


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    # Identity
    id: str                                    # Unique identifier
    name: str                                  # Human-readable name
    description: str = ""                      # What this server does

    # Transport configuration
    transport: MCPTransportType = MCPTransportType.STDIO

    # For STDIO transport
    command: Optional[str] = None              # e.g., "uvx", "npx", "python"
    args: List[str] = Field(default_factory=list)  # e.g., ["google-news-trends-mcp@latest"]
    env: Dict[str, str] = Field(default_factory=dict)  # Environment variables
    cwd: Optional[str] = None                  # Working directory

    # For SSE transport
    url: Optional[str] = None                  # Server URL
    headers: Dict[str, str] = Field(default_factory=dict)  # HTTP headers

    # Server settings
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # Available tools (discovered or pre-configured)
    tools: List[str] = Field(default_factory=list)

    # Cost tracking
    cost_per_call: float = 0.0                 # Estimated cost per tool call

    class Config:
        use_enum_values = True


class MCPToolConfig(BaseModel):
    """Configuration for using a specific MCP tool."""

    server_id: str                             # Which MCP server
    tool_name: str                             # Tool name on that server

    # Optional overrides
    timeout_seconds: Optional[int] = None

    # Parameter mappings (local param name -> MCP param name)
    param_mappings: Dict[str, str] = Field(default_factory=dict)

    # Default parameters to always pass
    default_params: Dict[str, Any] = Field(default_factory=dict)


class AgentMCPConfig(BaseModel):
    """MCP configuration for an agent."""

    # Enable/disable MCP for this agent
    enabled: bool = True

    # MCP servers this agent can use
    servers: List[str] = Field(default_factory=list)

    # Specific tool configurations
    tools: List[MCPToolConfig] = Field(default_factory=list)

    # Strategy settings
    prefer_mcp: bool = True                    # Prefer MCP over built-in
    fallback_to_builtin: bool = True           # Use built-in if MCP fails

    def get_tool_config(self, tool_name: str) -> Optional[MCPToolConfig]:
        """Get configuration for a specific tool."""
        for tool in self.tools:
            if tool.tool_name == tool_name:
                return tool
        return None


class MCPHealthStatus(BaseModel):
    """Health status of an MCP server."""

    server_id: str
    healthy: bool = False
    connected: bool = False
    tools_available: int = 0
    last_check: Optional[str] = None
    error: Optional[str] = None
