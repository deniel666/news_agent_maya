"""MCP server registry for Maya AI News Anchor.

This module provides centralized management of MCP servers including:
- Server registration and configuration
- Client lifecycle management
- Tool invocation with cost tracking
- Health monitoring
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .config import MCPServerConfig, MCPHealthStatus
from .client import MCPClient

logger = logging.getLogger(__name__)


class MCPRegistry:
    """Central registry for MCP server management."""

    def __init__(self):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._clients: Dict[str, MCPClient] = {}
        self._health_status: Dict[str, MCPHealthStatus] = {}
        self._call_logs: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # Server Registration
    # -------------------------------------------------------------------------

    def register_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server configuration."""
        self._servers[config.id] = config
        logger.info(f"Registered MCP server: {config.id} ({config.name})")

    def register_servers(self, configs: List[MCPServerConfig]) -> None:
        """Register multiple MCP server configurations."""
        for config in configs:
            self.register_server(config)

    def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server."""
        if server_id in self._servers:
            # Disconnect if connected
            if server_id in self._clients:
                asyncio.create_task(self._disconnect_client(server_id))
            del self._servers[server_id]
            if server_id in self._health_status:
                del self._health_status[server_id]
            logger.info(f"Unregistered MCP server: {server_id}")
            return True
        return False

    async def _disconnect_client(self, server_id: str) -> None:
        """Disconnect and remove a client."""
        if server_id in self._clients:
            try:
                await self._clients[server_id].disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting client {server_id}: {e}")
            del self._clients[server_id]

    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get server configuration."""
        return self._servers.get(server_id)

    def update_server_config(self, server_id: str, updates: Dict[str, Any]) -> Optional[MCPServerConfig]:
        """Update server configuration."""
        if server_id not in self._servers:
            return None
        config = self._servers[server_id]
        config_data = config.model_dump()
        config_data.update(updates)
        self._servers[server_id] = MCPServerConfig(**config_data)
        return self._servers[server_id]

    def list_servers(self) -> List[MCPServerConfig]:
        """List all registered servers."""
        return list(self._servers.values())

    def list_enabled_servers(self) -> List[MCPServerConfig]:
        """List only enabled servers."""
        return [s for s in self._servers.values() if s.enabled]

    def enable_server(self, server_id: str) -> bool:
        """Enable an MCP server."""
        if server_id in self._servers:
            self._servers[server_id].enabled = True
            return True
        return False

    def disable_server(self, server_id: str) -> bool:
        """Disable an MCP server."""
        if server_id in self._servers:
            self._servers[server_id].enabled = False
            # Disconnect if connected
            asyncio.create_task(self._disconnect_client(server_id))
            return True
        return False

    # -------------------------------------------------------------------------
    # Client Management
    # -------------------------------------------------------------------------

    async def get_client(self, server_id: str) -> Optional[MCPClient]:
        """Get or create a client for a server."""
        if server_id not in self._servers:
            logger.warning(f"Server not registered: {server_id}")
            return None

        config = self._servers[server_id]
        if not config.enabled:
            logger.warning(f"Server is disabled: {server_id}")
            return None

        if server_id not in self._clients:
            client = MCPClient(config)
            if await client.connect():
                self._clients[server_id] = client
            else:
                return None

        return self._clients[server_id]

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        agent_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Call a tool on an MCP server with logging.

        Args:
            server_id: ID of the MCP server
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            agent_id: ID of the calling agent (for logging)
            thread_id: Thread ID (for logging)

        Returns:
            Dictionary with 'success', 'content', and optionally 'error'
        """
        client = await self.get_client(server_id)
        if not client:
            return {"success": False, "error": f"Server not available: {server_id}"}

        start_time = datetime.utcnow()
        result = await client.call_tool(tool_name, arguments or {})
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log the call
        config = self._servers[server_id]
        log_entry = {
            "timestamp": start_time.isoformat(),
            "server_id": server_id,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "thread_id": thread_id,
            "success": result.get("success", False),
            "duration_seconds": duration,
            "estimated_cost": config.cost_per_call,
        }
        self._call_logs.append(log_entry)

        # Keep only last 1000 logs in memory
        if len(self._call_logs) > 1000:
            self._call_logs = self._call_logs[-1000:]

        return result

    def get_call_logs(
        self,
        server_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get MCP call logs with optional filtering."""
        logs = self._call_logs

        if server_id:
            logs = [l for l in logs if l["server_id"] == server_id]
        if agent_id:
            logs = [l for l in logs if l["agent_id"] == agent_id]

        return logs[-limit:]

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary from call logs."""
        total_calls = len(self._call_logs)
        successful_calls = len([l for l in self._call_logs if l["success"]])
        total_cost = sum(l.get("estimated_cost", 0) for l in self._call_logs)

        by_server = {}
        for log in self._call_logs:
            server_id = log["server_id"]
            if server_id not in by_server:
                by_server[server_id] = {"calls": 0, "cost": 0}
            by_server[server_id]["calls"] += 1
            by_server[server_id]["cost"] += log.get("estimated_cost", 0)

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "total_estimated_cost": total_cost,
            "by_server": by_server,
        }

    # -------------------------------------------------------------------------
    # Health Monitoring
    # -------------------------------------------------------------------------

    async def health_check(self, server_id: str) -> MCPHealthStatus:
        """Check health of an MCP server."""
        status = MCPHealthStatus(
            server_id=server_id,
            last_check=datetime.utcnow().isoformat(),
        )

        if server_id not in self._servers:
            status.error = "Server not registered"
            self._health_status[server_id] = status
            return status

        client = await self.get_client(server_id)

        if client and client.is_connected:
            status.healthy = True
            status.connected = True
            status.tools_available = len(client.list_tools())
        else:
            status.error = "Failed to connect"

        self._health_status[server_id] = status
        return status

    async def health_check_all(self) -> Dict[str, MCPHealthStatus]:
        """Check health of all registered servers."""
        tasks = [
            self.health_check(server_id)
            for server_id in self._servers
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        return self._health_status

    def get_health_status(self, server_id: str) -> Optional[MCPHealthStatus]:
        """Get cached health status for a server."""
        return self._health_status.get(server_id)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    async def startup(self) -> None:
        """Initialize all enabled MCP servers."""
        logger.info("Starting MCP registry...")
        for config in self.list_enabled_servers():
            try:
                await self.get_client(config.id)
                logger.info(f"Started MCP server: {config.id}")
            except Exception as e:
                logger.error(f"Failed to start MCP server {config.id}: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all MCP connections."""
        logger.info("Shutting down MCP registry...")
        for server_id in list(self._clients.keys()):
            try:
                await self._disconnect_client(server_id)
            except Exception as e:
                logger.warning(f"Error disconnecting MCP client {server_id}: {e}")
        self._clients.clear()


# Global registry instance
_mcp_registry: Optional[MCPRegistry] = None


def get_mcp_registry() -> MCPRegistry:
    """Get the global MCP registry instance."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPRegistry()
    return _mcp_registry


def reset_mcp_registry() -> None:
    """Reset the global MCP registry (for testing)."""
    global _mcp_registry
    if _mcp_registry:
        asyncio.create_task(_mcp_registry.shutdown())
    _mcp_registry = None
