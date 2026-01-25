from .pipeline import MayaPipeline, get_pipeline
from .config import (
    AgentConfig,
    SegmentConfig,
    LLMConfig,
    AgentType,
    get_config_manager,
)
from .registry import (
    AgentRegistry,
    get_registry,
    agent,
    with_llm,
)

# Legacy nodes (backward compatible)
from .nodes import (
    aggregate_news,
    deduplicate_articles,
    categorize_articles,
    synthesize_local,
    synthesize_business,
    synthesize_ai,
    generate_scripts,
    script_approval_gate,
    generate_video,
    video_approval_gate,
    publish_to_social,
)

# Media Machine agents (new architecture)
from .roles import (
    AgentRole,
    ROLE_METADATA,
    MEDIA_MACHINE_AGENTS,
    MEDIA_MACHINE_FLOW,
    get_role_metadata,
    get_role_by_agent_id,
    list_all_roles,
)

from .media_machine import (
    research_agent,
    editor_agent,
    writer_local_agent,
    writer_business_agent,
    writer_ai_agent,
    fact_checker_agent,
    script_assembler_agent,
    localization_agent,
    quality_control_gate,
    producer_agent,
    video_approval_gate as video_approval_gate_v2,
    social_media_agent,
    analytics_agent,
)

# Advanced features
from .cost_tracker import get_cost_tracker, CostTracker
from .ab_testing import get_ab_manager, Experiment, VariantConfig
from .plugins import get_plugin_manager, plugin_agent

__all__ = [
    # Pipeline
    "MayaPipeline",
    "get_pipeline",

    # Configuration
    "AgentConfig",
    "SegmentConfig",
    "LLMConfig",
    "AgentType",
    "get_config_manager",

    # Registry
    "AgentRegistry",
    "get_registry",
    "agent",
    "with_llm",

    # Legacy Nodes
    "aggregate_news",
    "deduplicate_articles",
    "categorize_articles",
    "synthesize_local",
    "synthesize_business",
    "synthesize_ai",
    "generate_scripts",
    "script_approval_gate",
    "generate_video",
    "video_approval_gate",
    "publish_to_social",

    # Media Machine Roles
    "AgentRole",
    "ROLE_METADATA",
    "MEDIA_MACHINE_AGENTS",
    "MEDIA_MACHINE_FLOW",
    "get_role_metadata",
    "get_role_by_agent_id",
    "list_all_roles",

    # Media Machine Agents
    "research_agent",
    "editor_agent",
    "writer_local_agent",
    "writer_business_agent",
    "writer_ai_agent",
    "fact_checker_agent",
    "script_assembler_agent",
    "localization_agent",
    "quality_control_gate",
    "producer_agent",
    "video_approval_gate_v2",
    "social_media_agent",
    "analytics_agent",

    # Advanced Features
    "get_cost_tracker",
    "CostTracker",
    "get_ab_manager",
    "Experiment",
    "VariantConfig",
    "get_plugin_manager",
    "plugin_agent",
]
