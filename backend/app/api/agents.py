"""API endpoints for agent configuration and management."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.agents.config import (
    AgentConfig,
    SegmentConfig,
    LLMConfig,
    PipelineFlowConfig,
    get_config_manager,
)
from app.agents.registry import get_registry

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AgentUpdateRequest(BaseModel):
    """Request to update agent configuration."""
    enabled: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    custom_prompt: Optional[str] = None
    max_items: Optional[int] = None
    params: Optional[Dict[str, Any]] = None


class LLMUpdateRequest(BaseModel):
    """Request to update agent LLM settings."""
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class SegmentUpdateRequest(BaseModel):
    """Request to update segment configuration."""
    enabled: Optional[bool] = None
    target_duration_seconds: Optional[int] = None
    target_word_count: Optional[int] = None
    max_articles: Optional[int] = None
    focus_topics: Optional[List[str]] = None
    avoid_topics: Optional[List[str]] = None
    order: Optional[int] = None


class NewSegmentRequest(BaseModel):
    """Request to create a new content segment."""
    id: str
    name: str
    target_duration_seconds: int = 60
    target_word_count: int = 150
    max_articles: int = 15
    order: int = 4
    focus_topics: List[str] = []
    avoid_topics: List[str] = []


class ConfigExportResponse(BaseModel):
    """Full configuration export."""
    agents: Dict[str, Any]
    segments: Dict[str, Any]
    pipeline_flow: Dict[str, Any]


# =============================================================================
# AGENT ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[Dict[str, Any]])
async def list_agents():
    """List all configured agents with their settings."""
    config_manager = get_config_manager()
    registry = get_registry()

    agents = []
    for agent in config_manager.list_agents():
        agent_dict = agent.model_dump()
        agent_dict["has_handler"] = registry.is_registered(agent.id)
        agents.append(agent_dict)

    return agents


@router.get("/enabled", response_model=List[Dict[str, Any]])
async def list_enabled_agents():
    """List only enabled agents."""
    config_manager = get_config_manager()
    return [a.model_dump() for a in config_manager.list_enabled_agents()]


@router.get("/{agent_id}", response_model=Dict[str, Any])
async def get_agent(agent_id: str):
    """Get configuration for a specific agent."""
    config_manager = get_config_manager()
    agent = config_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    registry = get_registry()
    result = agent.model_dump()
    result["has_handler"] = registry.is_registered(agent_id)
    return result


@router.patch("/{agent_id}", response_model=Dict[str, Any])
async def update_agent(agent_id: str, request: AgentUpdateRequest):
    """Update agent configuration."""
    config_manager = get_config_manager()

    if not config_manager.get_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    updates = request.model_dump(exclude_none=True)

    try:
        updated = config_manager.update_agent(agent_id, updates)
        return updated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/enable")
async def enable_agent(agent_id: str):
    """Enable an agent."""
    config_manager = get_config_manager()

    if not config_manager.get_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    config_manager.enable_agent(agent_id)
    return {"message": f"Agent {agent_id} enabled"}


@router.post("/{agent_id}/disable")
async def disable_agent(agent_id: str):
    """Disable an agent."""
    config_manager = get_config_manager()

    if not config_manager.get_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    config_manager.disable_agent(agent_id)
    return {"message": f"Agent {agent_id} disabled"}


@router.patch("/{agent_id}/llm", response_model=Dict[str, Any])
async def update_agent_llm(agent_id: str, request: LLMUpdateRequest):
    """Update LLM settings for an agent."""
    config_manager = get_config_manager()
    agent = config_manager.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    if not agent.llm_config:
        raise HTTPException(
            status_code=400,
            detail=f"Agent {agent_id} does not use LLM"
        )

    # Update LLM config
    llm_updates = request.model_dump(exclude_none=True)
    new_llm_config = LLMConfig(
        **{**agent.llm_config.model_dump(), **llm_updates}
    )

    updated = config_manager.update_agent(agent_id, {"llm_config": new_llm_config})
    return updated.model_dump()


# =============================================================================
# SEGMENT ENDPOINTS
# =============================================================================

@router.get("/segments/", response_model=List[Dict[str, Any]])
async def list_segments():
    """List all content segments."""
    config_manager = get_config_manager()
    return [s.model_dump() for s in config_manager.list_segments()]


@router.get("/segments/enabled", response_model=List[Dict[str, Any]])
async def list_enabled_segments():
    """List only enabled segments in order."""
    config_manager = get_config_manager()
    return [s.model_dump() for s in config_manager.list_enabled_segments()]


@router.get("/segments/{segment_id}", response_model=Dict[str, Any])
async def get_segment(segment_id: str):
    """Get configuration for a specific segment."""
    config_manager = get_config_manager()
    segment = config_manager.get_segment(segment_id)

    if not segment:
        raise HTTPException(status_code=404, detail=f"Segment not found: {segment_id}")

    return segment.model_dump()


@router.patch("/segments/{segment_id}", response_model=Dict[str, Any])
async def update_segment(segment_id: str, request: SegmentUpdateRequest):
    """Update segment configuration."""
    config_manager = get_config_manager()

    if not config_manager.get_segment(segment_id):
        raise HTTPException(status_code=404, detail=f"Segment not found: {segment_id}")

    updates = request.model_dump(exclude_none=True)

    try:
        updated = config_manager.update_segment(segment_id, updates)
        return updated.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/segments/", response_model=Dict[str, Any])
async def create_segment(request: NewSegmentRequest):
    """Create a new content segment.

    This also creates a corresponding synthesizer agent for the segment.
    """
    config_manager = get_config_manager()

    # Check if segment already exists
    if config_manager.get_segment(request.id):
        raise HTTPException(
            status_code=400,
            detail=f"Segment already exists: {request.id}"
        )

    segment = SegmentConfig(**request.model_dump())
    config_manager.add_segment(segment)

    return {
        "segment": segment.model_dump(),
        "synthesizer_agent": f"synthesize_{request.id}",
        "message": "Segment created. Note: You'll need to add a handler for the synthesizer agent."
    }


# =============================================================================
# PIPELINE FLOW ENDPOINTS
# =============================================================================

@router.get("/pipeline/flow", response_model=Dict[str, Any])
async def get_pipeline_flow():
    """Get current pipeline flow configuration."""
    config_manager = get_config_manager()
    flow_config = config_manager.get_pipeline_flow()
    execution_order = config_manager.get_execution_order()

    return {
        "config": flow_config.model_dump(),
        "execution_order": execution_order,
    }


@router.get("/pipeline/execution-order", response_model=List[List[str]])
async def get_execution_order():
    """Get flattened execution order with parallel groups."""
    config_manager = get_config_manager()
    return config_manager.get_execution_order()


# =============================================================================
# GLOBAL SETTINGS ENDPOINTS
# =============================================================================

@router.post("/settings/model")
async def set_global_model(model: str):
    """Set the LLM model for all synthesizer/analyzer agents."""
    config_manager = get_config_manager()
    config_manager.set_global_model(model)
    return {"message": f"Global model set to {model}"}


@router.post("/settings/reset")
async def reset_to_defaults():
    """Reset all agent configurations to defaults."""
    config_manager = get_config_manager()
    config_manager.reset_to_defaults()
    return {"message": "Configuration reset to defaults"}


# =============================================================================
# EXPORT/IMPORT ENDPOINTS
# =============================================================================

@router.get("/config/export", response_model=ConfigExportResponse)
async def export_config():
    """Export full configuration as JSON."""
    config_manager = get_config_manager()
    return config_manager.export_config()


@router.post("/config/import")
async def import_config(config: Dict[str, Any]):
    """Import configuration from JSON.

    Warning: This will overwrite existing configuration.
    """
    config_manager = get_config_manager()

    try:
        config_manager.import_config(config)
        return {"message": "Configuration imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


# =============================================================================
# REGISTRY INFO ENDPOINTS
# =============================================================================

@router.get("/registry/handlers")
async def list_registered_handlers():
    """List all registered agent handlers."""
    registry = get_registry()
    return {"handlers": registry.list_registered()}


@router.get("/registry/status")
async def get_registry_status():
    """Get overall registry status."""
    config_manager = get_config_manager()
    registry = get_registry()

    configured_agents = set(a.id for a in config_manager.list_agents())
    registered_handlers = set(registry.list_registered())

    return {
        "configured_agents": len(configured_agents),
        "registered_handlers": len(registered_handlers),
        "missing_handlers": list(configured_agents - registered_handlers),
        "extra_handlers": list(registered_handlers - configured_agents),
    }
