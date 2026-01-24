"""MCP client implementation for Maya AI News Anchor.

This module provides the MCPClient class for communicating with MCP servers
via stdio transport (subprocess management).
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List

from .config import MCPServerConfig, MCPTransportType

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for communicating with a single MCP server via stdio."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._tools: Dict[str, Any] = {}
        self._request_id = 0
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._process is not None

    async def connect(self) -> bool:
        """Establish connection to the MCP server."""
        if self._connected:
            return True

        if self.config.transport != MCPTransportType.STDIO:
            logger.error(f"Unsupported transport: {self.config.transport}")
            return False

        if not self.config.command:
            logger.error(f"No command specified for server: {self.config.id}")
            return False

        try:
            # Prepare environment with variable substitution
            env = os.environ.copy()
            for key, value in self.config.env.items():
                # Substitute ${VAR} with environment variable
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    env[key] = os.environ.get(env_var, "")
                else:
                    env[key] = value

            # Start the subprocess
            cmd = [self.config.command] + self.config.args
            logger.info(f"Starting MCP server {self.config.id}: {' '.join(cmd)}")

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.config.cwd,
                text=True,
                bufsize=1,
            )

            # Initialize MCP session
            await self._initialize()

            self._connected = True
            logger.info(f"Connected to MCP server: {self.config.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.config.id}: {e}")
            await self.disconnect()
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"Error terminating MCP process: {e}")
                try:
                    self._process.kill()
                except Exception:
                    pass
            self._process = None
        self._connected = False
        self._tools.clear()

    async def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("MCP server not connected")

        async with self._lock:
            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params or {},
            }

            try:
                # Send request
                request_str = json.dumps(request) + "\n"
                self._process.stdin.write(request_str)
                self._process.stdin.flush()

                # Read response (with timeout)
                loop = asyncio.get_event_loop()
                response_str = await asyncio.wait_for(
                    loop.run_in_executor(None, self._process.stdout.readline),
                    timeout=self.config.timeout_seconds
                )

                if not response_str:
                    raise RuntimeError("Empty response from MCP server")

                response = json.loads(response_str)

                if "error" in response:
                    raise RuntimeError(f"MCP error: {response['error']}")

                return response.get("result", {})

            except asyncio.TimeoutError:
                raise RuntimeError(f"MCP request timed out: {method}")
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON response: {e}")

    async def _initialize(self) -> None:
        """Initialize MCP session and discover tools."""
        # Send initialize request
        await self._send_request(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "clientInfo": {
                    "name": "maya-news-anchor",
                    "version": "1.0.0",
                }
            }
        )

        # Send initialized notification (no response expected)
        try:
            init_notif = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            self._process.stdin.write(json.dumps(init_notif) + "\n")
            self._process.stdin.flush()
        except Exception:
            pass  # Notification, no response expected

        # Discover available tools
        try:
            tools_response = await self._send_request(
                method="tools/list",
                params={}
            )

            for tool in tools_response.get("tools", []):
                self._tools[tool["name"]] = tool

            logger.info(f"Discovered {len(self._tools)} tools on {self.config.id}: {list(self._tools.keys())}")
        except Exception as e:
            logger.warning(f"Failed to discover tools on {self.config.id}: {e}")
            # Use pre-configured tools if discovery fails
            for tool_name in self.config.tools:
                self._tools[tool_name] = {"name": tool_name}

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            timeout: Optional timeout override

        Returns:
            Dictionary with 'success', 'content', and optionally 'error'
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return {"success": False, "error": "Failed to connect to MCP server"}

        if tool_name not in self._tools:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        original_timeout = self.config.timeout_seconds
        if timeout:
            self.config.timeout_seconds = timeout

        try:
            response = await self._send_request(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments or {},
                }
            )

            return {
                "success": True,
                "content": response.get("content", []),
                "isError": response.get("isError", False),
            }

        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.config.timeout_seconds = original_timeout

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the input schema for a tool."""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List available tools."""
        return list(self._tools.keys())

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available."""
        return tool_name in self._tools
