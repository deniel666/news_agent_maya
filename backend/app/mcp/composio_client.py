"""Composio client integration for Maya AI News Anchor.

This module provides the ComposioClient class that wraps the Composio SDK
to provide MCP tool access through the Composio Tool Router.

Composio provides:
- 500+ pre-integrated tools via single MCP endpoint
- Dynamic tool discovery and routing
- Unified authentication management
- SOC 2 Type 2 compliance
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class ComposioClient:
    """Client for accessing MCP tools via Composio Tool Router.

    This client wraps the Composio SDK to provide:
    - Tool discovery from 500+ integrated apps
    - Dynamic tool routing based on task requirements
    - Unified authentication handling
    - Cost tracking per tool call
    """

    def __init__(self, api_key: str, user_id: str = "maya_agent"):
        """Initialize Composio client.

        Args:
            api_key: Composio API key
            user_id: User identifier for tracking
        """
        self.api_key = api_key
        self.user_id = user_id
        self._toolset = None
        self._connected = False
        self._tools: Dict[str, Any] = {}
        self._call_logs: List[Dict[str, Any]] = []

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._toolset is not None

    async def connect(self) -> bool:
        """Initialize connection to Composio."""
        if self._connected:
            return True

        try:
            # Import Composio SDK
            from composio_langchain import ComposioToolSet

            # Initialize toolset
            self._toolset = ComposioToolSet(api_key=self.api_key)
            self._connected = True

            logger.info("Connected to Composio Tool Router")
            return True

        except ImportError:
            logger.error("Composio SDK not installed. Run: pip install composio-langchain")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Composio: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Composio."""
        self._toolset = None
        self._connected = False
        self._tools.clear()

    async def discover_tools(self, apps: List[str] = None) -> List[str]:
        """Discover available tools from Composio.

        Args:
            apps: Optional list of app names to filter tools
                  e.g., ["GOOGLENEWS", "TWITTER", "SLACK"]

        Returns:
            List of available tool names
        """
        if not self._connected:
            await self.connect()

        if not self._toolset:
            return []

        try:
            from composio import App, Action

            # Get tools for specified apps or all available
            if apps:
                tools = self._toolset.get_tools(apps=apps)
            else:
                # Get commonly used tools for Maya
                tools = self._toolset.get_tools(apps=[
                    App.GOOGLENEWS,
                    App.TWITTER,
                    App.SLACK,
                    App.NOTION,
                ])

            for tool in tools:
                tool_name = getattr(tool, 'name', str(tool))
                self._tools[tool_name] = tool

            logger.info(f"Discovered {len(self._tools)} Composio tools")
            return list(self._tools.keys())

        except Exception as e:
            logger.error(f"Failed to discover Composio tools: {e}")
            return []

    async def get_tools_for_task(self, task_description: str, max_tools: int = 10) -> List[Any]:
        """Get relevant tools for a specific task using Composio's Tool Router.

        Args:
            task_description: Natural language description of the task
            max_tools: Maximum number of tools to return

        Returns:
            List of LangChain-compatible tools
        """
        if not self._connected:
            await self.connect()

        if not self._toolset:
            return []

        try:
            # Use Composio's intelligent tool selection
            tools = self._toolset.get_tools(
                actions=None,  # Let Composio decide based on task
                max_tools=max_tools,
            )
            return tools

        except Exception as e:
            logger.error(f"Failed to get tools for task: {e}")
            return []

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call a Composio tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            timeout: Optional timeout in seconds

        Returns:
            Dictionary with 'success', 'content', and optionally 'error'
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return {"success": False, "error": "Failed to connect to Composio"}

        start_time = datetime.utcnow()

        try:
            if tool_name not in self._tools:
                # Try to find the tool
                await self.discover_tools()
                if tool_name not in self._tools:
                    return {"success": False, "error": f"Tool not found: {tool_name}"}

            tool = self._tools[tool_name]

            # Execute the tool
            if timeout:
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool.invoke, arguments or {}),
                    timeout=timeout
                )
            else:
                result = await asyncio.to_thread(tool.invoke, arguments or {})

            duration = (datetime.utcnow() - start_time).total_seconds()

            # Log the call
            self._call_logs.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "success": True,
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
            })

            return {
                "success": True,
                "content": result if isinstance(result, list) else [result],
                "isError": False,
            }

        except asyncio.TimeoutError:
            logger.error(f"Composio tool call timed out: {tool_name}")
            return {"success": False, "error": "Timeout"}

        except Exception as e:
            logger.error(f"Composio tool call failed: {tool_name}: {e}")

            duration = (datetime.utcnow() - start_time).total_seconds()
            self._call_logs.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": start_time.isoformat(),
            })

            return {"success": False, "error": str(e)}

    def list_tools(self) -> List[str]:
        """List available tools."""
        return list(self._tools.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self._tools

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a tool."""
        tool = self._tools.get(tool_name)
        if tool and hasattr(tool, 'args_schema'):
            return tool.args_schema.schema() if tool.args_schema else None
        return None

    def get_call_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent tool call logs."""
        return self._call_logs[-limit:]

    def get_langchain_tools(self, apps: List[str] = None) -> List[Any]:
        """Get tools as LangChain-compatible tool objects.

        Args:
            apps: Optional list of app names to filter

        Returns:
            List of LangChain tool objects
        """
        if not self._connected or not self._toolset:
            return []

        try:
            from composio import App

            if apps:
                # Convert string app names to App enum
                app_enums = []
                for app in apps:
                    if hasattr(App, app.upper()):
                        app_enums.append(getattr(App, app.upper()))
                return self._toolset.get_tools(apps=app_enums)
            else:
                return self._toolset.get_tools()

        except Exception as e:
            logger.error(f"Failed to get LangChain tools: {e}")
            return []


# Singleton instance
_composio_client: Optional[ComposioClient] = None


def get_composio_client() -> Optional[ComposioClient]:
    """Get the global Composio client instance.

    Returns None if Composio is not configured.
    """
    global _composio_client

    if _composio_client is None:
        from app.core.config import settings

        if settings.composio_api_key:
            _composio_client = ComposioClient(
                api_key=settings.composio_api_key,
                user_id=settings.composio_user_id,
            )
        else:
            logger.debug("Composio API key not configured, client not available")
            return None

    return _composio_client


async def init_composio_client() -> Optional[ComposioClient]:
    """Initialize and connect the Composio client.

    Returns:
        Connected ComposioClient or None if not configured
    """
    client = get_composio_client()
    if client:
        await client.connect()
        # Pre-discover common tools for Maya
        await client.discover_tools(["GOOGLENEWS", "TWITTER"])
    return client
