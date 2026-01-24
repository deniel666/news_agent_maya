"""MCP management API endpoints for Maya AI News Anchor.

This module provides REST API endpoints for:
- Server management (list, register, enable/disable)
- Tool discovery and invocation
- Health monitoring
- Cost tracking
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.mcp.registry import get_mcp_registry
from app.mcp.config import MCPServerConfig, MCPTransportType, MCPHealthStatus
from app.mcp.defaults import DEFAULT_MCP_SERVERS

router = APIRouter(prefix="/mcp", tags=["MCP"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class MCPServerRequest(BaseModel):
    """Request to register an MCP server."""
    id: str
    name: str
    description: str = ""
    transport: str = "stdio"
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    url: Optional[str] = None
    enabled: bool = True
    timeout_seconds: int = 30
    tools: List[str] = Field(default_factory=list)
    cost_per_call: float = 0.0


class MCPToolCallRequest(BaseModel):
    """Request to call an MCP tool."""
    server_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = None
    thread_id: Optional[str] = None


class MCPServerUpdateRequest(BaseModel):
    """Request to update server configuration."""
    enabled: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    cost_per_call: Optional[float] = None


# =============================================================================
# SERVER MANAGEMENT
# =============================================================================

@router.get("/servers", response_model=List[Dict[str, Any]])
async def list_servers():
    """List all registered MCP servers."""
    registry = get_mcp_registry()
    return [s.model_dump() for s in registry.list_servers()]


@router.get("/servers/enabled", response_model=List[Dict[str, Any]])
async def list_enabled_servers():
    """List only enabled MCP servers."""
    registry = get_mcp_registry()
    return [s.model_dump() for s in registry.list_enabled_servers()]


@router.get("/servers/{server_id}")
async def get_server(server_id: str):
    """Get details of a specific MCP server."""
    registry = get_mcp_registry()
    config = registry.get_server_config(server_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    return config.model_dump()


@router.post("/servers", response_model=Dict[str, Any])
async def register_server(request: MCPServerRequest):
    """Register a new MCP server."""
    registry = get_mcp_registry()

    # Check if already exists
    if registry.get_server_config(request.id):
        raise HTTPException(
            status_code=400,
            detail=f"Server already exists: {request.id}"
        )

    config = MCPServerConfig(
        id=request.id,
        name=request.name,
        description=request.description,
        transport=MCPTransportType(request.transport),
        command=request.command,
        args=request.args,
        env=request.env,
        url=request.url,
        enabled=request.enabled,
        timeout_seconds=request.timeout_seconds,
        tools=request.tools,
        cost_per_call=request.cost_per_call,
    )

    registry.register_server(config)
    return {"message": f"Server {request.id} registered", "config": config.model_dump()}


@router.patch("/servers/{server_id}")
async def update_server(server_id: str, request: MCPServerUpdateRequest):
    """Update MCP server configuration."""
    registry = get_mcp_registry()

    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    config = registry.update_server_config(server_id, updates)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    return {"message": f"Server {server_id} updated", "config": config.model_dump()}


@router.delete("/servers/{server_id}")
async def unregister_server(server_id: str):
    """Unregister an MCP server."""
    registry = get_mcp_registry()
    if registry.unregister_server(server_id):
        return {"message": f"Server {server_id} unregistered"}
    raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")


@router.post("/servers/{server_id}/enable")
async def enable_server(server_id: str, background_tasks: BackgroundTasks):
    """Enable an MCP server and attempt connection."""
    registry = get_mcp_registry()

    if not registry.get_server_config(server_id):
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    registry.enable_server(server_id)

    # Try to connect in background
    background_tasks.add_task(registry.get_client, server_id)

    return {"message": f"Server {server_id} enabled"}


@router.post("/servers/{server_id}/disable")
async def disable_server(server_id: str):
    """Disable an MCP server and disconnect."""
    registry = get_mcp_registry()

    if not registry.disable_server(server_id):
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")

    return {"message": f"Server {server_id} disabled"}


# =============================================================================
# TOOL DISCOVERY & INVOCATION
# =============================================================================

@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: str):
    """List available tools on an MCP server."""
    registry = get_mcp_registry()
    client = await registry.get_client(server_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Server not available: {server_id}"
        )

    return {"server_id": server_id, "tools": client.list_tools()}


@router.get("/servers/{server_id}/tools/{tool_name}/schema")
async def get_tool_schema(server_id: str, tool_name: str):
    """Get the input schema for a tool."""
    registry = get_mcp_registry()
    client = await registry.get_client(server_id)

    if not client:
        raise HTTPException(
            status_code=404,
            detail=f"Server not available: {server_id}"
        )

    schema = client.get_tool_schema(tool_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    return schema


@router.post("/tools/call")
async def call_tool(request: MCPToolCallRequest):
    """Call a tool on an MCP server."""
    registry = get_mcp_registry()

    result = await registry.call_tool(
        server_id=request.server_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
        agent_id=request.agent_id,
        thread_id=request.thread_id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Tool call failed")
        )

    return result


# =============================================================================
# HEALTH & MONITORING
# =============================================================================

@router.get("/health")
async def health_check_all():
    """Check health of all MCP servers."""
    registry = get_mcp_registry()
    statuses = await registry.health_check_all()
    return {
        server_id: status.model_dump()
        for server_id, status in statuses.items()
    }


@router.get("/health/{server_id}")
async def health_check(server_id: str):
    """Check health of a specific MCP server."""
    registry = get_mcp_registry()
    status = await registry.health_check(server_id)
    return status.model_dump()


# =============================================================================
# COST TRACKING
# =============================================================================

@router.get("/costs/summary")
async def get_cost_summary():
    """Get MCP cost summary."""
    registry = get_mcp_registry()
    return registry.get_cost_summary()


@router.get("/costs/logs")
async def get_cost_logs(
    server_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    limit: int = 100,
):
    """Get MCP call logs with optional filtering."""
    registry = get_mcp_registry()
    return registry.get_call_logs(
        server_id=server_id,
        agent_id=agent_id,
        limit=limit,
    )


# =============================================================================
# INITIALIZATION
# =============================================================================

@router.post("/init")
async def initialize_default_servers(background_tasks: BackgroundTasks):
    """Initialize default MCP servers."""
    registry = get_mcp_registry()

    registered = []
    for config in DEFAULT_MCP_SERVERS:
        if not registry.get_server_config(config.id):
            registry.register_server(config)
            registered.append(config.id)

    # Start enabled servers in background
    background_tasks.add_task(registry.startup)

    return {
        "message": "Default servers initialized",
        "registered": registered,
        "total_servers": len(registry.list_servers()),
    }


@router.get("/defaults")
async def list_default_servers():
    """List available default MCP server configurations."""
    return [
        {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "enabled": config.enabled,
            "cost_per_call": config.cost_per_call,
            "tools": config.tools,
        }
        for config in DEFAULT_MCP_SERVERS
    ]
