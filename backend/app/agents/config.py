"""Agent configuration system for Maya AI News Anchor.

This module provides a flexible, configurable agent architecture that allows:
- Dynamic agent registration and configuration
- Per-agent LLM settings (model, temperature, max_tokens)
- Enable/disable agents without code changes
- Custom prompts and parameters per agent
- Pipeline flow customization
- MCP server integration for enhanced capabilities
"""

from typing import Dict, Any, Optional, List, Callable, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum

if TYPE_CHECKING:
    from app.mcp.config import AgentMCPConfig


class AgentType(str, Enum):
    """Types of agents in the Maya pipeline."""
    AGGREGATOR = "aggregator"           # Fetches content from sources
    PROCESSOR = "processor"             # Transforms/processes content
    SYNTHESIZER = "synthesizer"         # Generates content with LLM
    GATE = "gate"                       # Human approval checkpoint
    PUBLISHER = "publisher"             # Outputs to external services
    ANALYZER = "analyzer"               # Analyzes/scores content


class LLMConfig(BaseModel):
    """Configuration for LLM-powered agents."""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Fallback model if primary fails
    fallback_model: Optional[str] = "gpt-4o-mini"

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


class AgentConfig(BaseModel):
    """Configuration for a single agent in the pipeline."""
    # Identity
    id: str
    name: str
    description: str
    agent_type: AgentType

    # Execution settings
    enabled: bool = True
    timeout_seconds: int = 300

    # LLM settings (for synthesizer/analyzer types)
    llm_config: Optional[LLMConfig] = None

    # Custom prompt (overrides default)
    custom_prompt: Optional[str] = None

    # Processing limits
    max_items: Optional[int] = None          # Max items to process
    min_items: Optional[int] = None          # Min items required

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)

    # Output configuration
    output_field: Optional[str] = None       # State field to write to

    # Custom parameters (agent-specific)
    params: Dict[str, Any] = Field(default_factory=dict)

    # MCP Configuration (for agents using MCP tools)
    mcp_config: Optional[Any] = None  # AgentMCPConfig when set

    class Config:
        use_enum_values = True

    def uses_mcp(self) -> bool:
        """Check if this agent uses MCP tools."""
        if self.mcp_config is None:
            return False
        return getattr(self.mcp_config, 'enabled', False)

    def get_mcp_servers(self) -> List[str]:
        """Get list of MCP server IDs this agent uses."""
        if not self.uses_mcp():
            return []
        return getattr(self.mcp_config, 'servers', [])

    def prefers_mcp(self) -> bool:
        """Check if this agent prefers MCP over built-in implementations."""
        if not self.uses_mcp():
            return False
        return getattr(self.mcp_config, 'prefer_mcp', True)

    def should_fallback_to_builtin(self) -> bool:
        """Check if agent should fallback to built-in when MCP fails."""
        if not self.uses_mcp():
            return True
        return getattr(self.mcp_config, 'fallback_to_builtin', True)


class PipelineFlowConfig(BaseModel):
    """Configuration for pipeline flow and routing."""
    # Sequential flow (list of agent IDs or parallel groups)
    # Example: ["aggregate", ["synthesize_local", "synthesize_business"], "generate_scripts"]
    flow: List[Any] = Field(default_factory=list)

    # Conditional routing rules
    conditional_routes: Dict[str, Dict[str, str]] = Field(default_factory=dict)

    # Interrupt points (agents that pause for human input)
    interrupt_points: List[str] = Field(default_factory=list)


class SegmentConfig(BaseModel):
    """Configuration for a content segment (local, business, ai_tech)."""
    id: str
    name: str
    enabled: bool = True

    # Synthesis settings
    target_duration_seconds: int = 60
    target_word_count: int = 150

    # Article selection
    max_articles: int = 15
    min_relevance_score: float = 0.3

    # Custom prompt additions
    focus_topics: List[str] = Field(default_factory=list)
    avoid_topics: List[str] = Field(default_factory=list)

    # Output position in final script (1, 2, 3, etc.)
    order: int = 1


# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

DEFAULT_LLM_CONFIG = LLMConfig(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=2000,
)

CREATIVE_LLM_CONFIG = LLMConfig(
    model="gpt-4o",
    temperature=0.9,
    max_tokens=2000,
)

ANALYTICAL_LLM_CONFIG = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.3,
    max_tokens=500,
)


# Default agent configurations
DEFAULT_AGENTS: Dict[str, AgentConfig] = {
    "aggregate": AgentConfig(
        id="aggregate",
        name="News Aggregator",
        description="Fetches news articles from configured sources (RSS, Telegram, Twitter)",
        agent_type=AgentType.AGGREGATOR,
        timeout_seconds=120,
        params={
            "lookback_days": 7,
            "sources": ["rss", "telegram", "twitter"],
        },
        output_field="raw_articles",
    ),

    "deduplicate": AgentConfig(
        id="deduplicate",
        name="Article Deduplicator",
        description="Removes duplicate articles based on title similarity",
        agent_type=AgentType.PROCESSOR,
        timeout_seconds=30,
        params={
            "similarity_threshold": 0.85,
            "use_embeddings": False,  # Set True for semantic deduplication
        },
    ),

    "categorize": AgentConfig(
        id="categorize",
        name="Article Categorizer",
        description="Categorizes articles into local, business, and ai_tech segments",
        agent_type=AgentType.ANALYZER,
        llm_config=ANALYTICAL_LLM_CONFIG,
        timeout_seconds=180,
        max_items=50,  # Process top 50 to save costs
        params={
            "categories": ["local", "business", "ai_tech"],
            "also_score_relevance": True,
        },
    ),

    "synthesize_local": AgentConfig(
        id="synthesize_local",
        name="Local News Synthesizer",
        description="Generates the local & international news segment script",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=DEFAULT_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,  # Top 10 articles for synthesis
        output_field="local_script",
        depends_on=["categorize"],
    ),

    "synthesize_business": AgentConfig(
        id="synthesize_business",
        name="Business News Synthesizer",
        description="Generates the business news segment script",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=DEFAULT_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,
        output_field="business_script",
        depends_on=["categorize"],
    ),

    "synthesize_ai": AgentConfig(
        id="synthesize_ai",
        name="AI & Tech Synthesizer",
        description="Generates the AI & technology news segment script",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=DEFAULT_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,
        output_field="ai_script",
        depends_on=["categorize"],
    ),

    "generate_scripts": AgentConfig(
        id="generate_scripts",
        name="Script Assembler",
        description="Combines segment scripts and generates social caption",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=60,
        depends_on=["synthesize_local", "synthesize_business", "synthesize_ai"],
        output_field="full_script",
    ),

    "script_approval": AgentConfig(
        id="script_approval",
        name="Script Approval Gate",
        description="Human approval checkpoint for generated scripts",
        agent_type=AgentType.GATE,
        timeout_seconds=86400,  # 24 hours
        depends_on=["generate_scripts"],
        params={
            "notification_channels": ["slack", "telegram"],
            "auto_approve_after_hours": None,  # Set to auto-approve
            "require_feedback_on_reject": True,
        },
    ),

    "generate_video": AgentConfig(
        id="generate_video",
        name="Video Generator",
        description="Generates AI avatar video using HeyGen",
        agent_type=AgentType.PUBLISHER,
        timeout_seconds=600,  # 10 minutes for video generation
        depends_on=["script_approval"],
        params={
            "aspect_ratio": "9:16",  # Vertical for social
            "background_color": "#1a1a2e",
            "max_wait_seconds": 600,
        },
        output_field="video_url",
    ),

    "video_approval": AgentConfig(
        id="video_approval",
        name="Video Approval Gate",
        description="Human approval checkpoint for generated video",
        agent_type=AgentType.GATE,
        timeout_seconds=86400,
        depends_on=["generate_video"],
        params={
            "notification_channels": ["slack", "telegram"],
        },
    ),

    "publish": AgentConfig(
        id="publish",
        name="Social Publisher",
        description="Publishes video to social media platforms",
        agent_type=AgentType.PUBLISHER,
        timeout_seconds=120,
        depends_on=["video_approval"],
        params={
            "platforms": ["instagram", "tiktok", "youtube", "linkedin"],
            "schedule_delay_minutes": 0,  # 0 = immediate
        },
        output_field="post_results",
    ),
}


# Default segment configurations
DEFAULT_SEGMENTS: Dict[str, SegmentConfig] = {
    "local": SegmentConfig(
        id="local",
        name="Local & International News",
        target_duration_seconds=60,
        target_word_count=150,
        max_articles=15,
        order=1,
        focus_topics=["Malaysia", "Singapore", "ASEAN", "government policy", "SME impact"],
    ),

    "business": SegmentConfig(
        id="business",
        name="Business News",
        target_duration_seconds=50,
        target_word_count=130,
        max_articles=15,
        order=2,
        focus_topics=["SME", "costs", "grants", "hiring", "economy", "ringgit"],
    ),

    "ai_tech": SegmentConfig(
        id="ai_tech",
        name="AI & Technology",
        target_duration_seconds=50,
        target_word_count=130,
        max_articles=15,
        order=3,
        focus_topics=["AI tools", "free tools", "WhatsApp", "social media", "e-commerce"],
        avoid_topics=["enterprise software", "cryptocurrency", "blockchain"],
    ),
}


# Default pipeline flow
DEFAULT_PIPELINE_FLOW = PipelineFlowConfig(
    flow=[
        "aggregate",
        "deduplicate",
        "categorize",
        ["synthesize_local", "synthesize_business", "synthesize_ai"],  # Parallel
        "generate_scripts",
        "script_approval",
        "generate_video",
        "video_approval",
        "publish",
    ],
    interrupt_points=["script_approval", "video_approval"],
    conditional_routes={
        "script_approval": {
            "approved": "generate_video",
            "rejected": "__end__",
        },
        "video_approval": {
            "approved": "publish",
            "rejected": "__end__",
        },
    },
)


# =============================================================================
# CONFIGURATION MANAGER
# =============================================================================

class AgentConfigManager:
    """Manages agent configurations with runtime updates."""

    def __init__(self):
        self._agents: Dict[str, AgentConfig] = DEFAULT_AGENTS.copy()
        self._segments: Dict[str, SegmentConfig] = DEFAULT_SEGMENTS.copy()
        self._pipeline_flow: PipelineFlowConfig = DEFAULT_PIPELINE_FLOW.model_copy()
        self._custom_agents: Dict[str, Callable] = {}

    # -------------------------------------------------------------------------
    # Agent Management
    # -------------------------------------------------------------------------

    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentConfig]:
        """List all configured agents."""
        return list(self._agents.values())

    def list_enabled_agents(self) -> List[AgentConfig]:
        """List only enabled agents."""
        return [a for a in self._agents.values() if a.enabled]

    def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> AgentConfig:
        """Update agent configuration."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        agent = self._agents[agent_id]
        updated_data = agent.model_dump()
        updated_data.update(updates)
        self._agents[agent_id] = AgentConfig(**updated_data)
        return self._agents[agent_id]

    def enable_agent(self, agent_id: str) -> None:
        """Enable an agent."""
        self.update_agent(agent_id, {"enabled": True})

    def disable_agent(self, agent_id: str) -> None:
        """Disable an agent."""
        self.update_agent(agent_id, {"enabled": False})

    def register_agent(self, config: AgentConfig, handler: Optional[Callable] = None) -> None:
        """Register a new agent with optional custom handler."""
        self._agents[config.id] = config
        if handler:
            self._custom_agents[config.id] = handler

    def get_custom_handler(self, agent_id: str) -> Optional[Callable]:
        """Get custom handler for an agent."""
        return self._custom_agents.get(agent_id)

    # -------------------------------------------------------------------------
    # Segment Management
    # -------------------------------------------------------------------------

    def get_segment(self, segment_id: str) -> Optional[SegmentConfig]:
        """Get configuration for a content segment."""
        return self._segments.get(segment_id)

    def list_segments(self) -> List[SegmentConfig]:
        """List all segments ordered by position."""
        return sorted(self._segments.values(), key=lambda s: s.order)

    def list_enabled_segments(self) -> List[SegmentConfig]:
        """List enabled segments ordered by position."""
        return sorted(
            [s for s in self._segments.values() if s.enabled],
            key=lambda s: s.order
        )

    def update_segment(self, segment_id: str, updates: Dict[str, Any]) -> SegmentConfig:
        """Update segment configuration."""
        if segment_id not in self._segments:
            raise ValueError(f"Segment not found: {segment_id}")

        segment = self._segments[segment_id]
        updated_data = segment.model_dump()
        updated_data.update(updates)
        self._segments[segment_id] = SegmentConfig(**updated_data)
        return self._segments[segment_id]

    def add_segment(self, config: SegmentConfig) -> None:
        """Add a new content segment."""
        self._segments[config.id] = config

        # Auto-create synthesizer agent for new segment
        synth_agent = AgentConfig(
            id=f"synthesize_{config.id}",
            name=f"{config.name} Synthesizer",
            description=f"Generates the {config.name} segment script",
            agent_type=AgentType.SYNTHESIZER,
            llm_config=DEFAULT_LLM_CONFIG,
            timeout_seconds=120,
            max_items=config.max_articles,
            output_field=f"{config.id}_script",
            depends_on=["categorize"],
        )
        self.register_agent(synth_agent)

    # -------------------------------------------------------------------------
    # Pipeline Flow Management
    # -------------------------------------------------------------------------

    def get_pipeline_flow(self) -> PipelineFlowConfig:
        """Get current pipeline flow configuration."""
        return self._pipeline_flow

    def update_pipeline_flow(self, updates: Dict[str, Any]) -> PipelineFlowConfig:
        """Update pipeline flow configuration."""
        updated_data = self._pipeline_flow.model_dump()
        updated_data.update(updates)
        self._pipeline_flow = PipelineFlowConfig(**updated_data)
        return self._pipeline_flow

    def get_execution_order(self) -> List[List[str]]:
        """Get flattened execution order with parallel groups."""
        result = []
        for item in self._pipeline_flow.flow:
            if isinstance(item, list):
                # Parallel group - filter to enabled agents
                enabled = [a for a in item if self.get_agent(a) and self.get_agent(a).enabled]
                if enabled:
                    result.append(enabled)
            else:
                # Single agent
                agent = self.get_agent(item)
                if agent and agent.enabled:
                    result.append([item])
        return result

    # -------------------------------------------------------------------------
    # LLM Configuration Helpers
    # -------------------------------------------------------------------------

    def set_global_model(self, model: str) -> None:
        """Set the LLM model for all synthesizer/analyzer agents."""
        for agent_id, agent in self._agents.items():
            if agent.llm_config and agent.agent_type in [AgentType.SYNTHESIZER, AgentType.ANALYZER]:
                self.update_agent(agent_id, {
                    "llm_config": LLMConfig(
                        **{**agent.llm_config.model_dump(), "model": model}
                    )
                })

    def set_agent_temperature(self, agent_id: str, temperature: float) -> None:
        """Set temperature for a specific agent."""
        agent = self.get_agent(agent_id)
        if agent and agent.llm_config:
            new_config = LLMConfig(
                **{**agent.llm_config.model_dump(), "temperature": temperature}
            )
            self.update_agent(agent_id, {"llm_config": new_config})

    # -------------------------------------------------------------------------
    # Configuration Export/Import
    # -------------------------------------------------------------------------

    def export_config(self) -> Dict[str, Any]:
        """Export full configuration as dictionary."""
        return {
            "agents": {k: v.model_dump() for k, v in self._agents.items()},
            "segments": {k: v.model_dump() for k, v in self._segments.items()},
            "pipeline_flow": self._pipeline_flow.model_dump(),
        }

    def import_config(self, config: Dict[str, Any]) -> None:
        """Import configuration from dictionary."""
        if "agents" in config:
            for agent_id, agent_data in config["agents"].items():
                self._agents[agent_id] = AgentConfig(**agent_data)

        if "segments" in config:
            for segment_id, segment_data in config["segments"].items():
                self._segments[segment_id] = SegmentConfig(**segment_data)

        if "pipeline_flow" in config:
            self._pipeline_flow = PipelineFlowConfig(**config["pipeline_flow"])

    def reset_to_defaults(self) -> None:
        """Reset all configurations to defaults."""
        self._agents = DEFAULT_AGENTS.copy()
        self._segments = DEFAULT_SEGMENTS.copy()
        self._pipeline_flow = DEFAULT_PIPELINE_FLOW.model_copy()
        self._custom_agents = {}


# Global configuration manager instance
_config_manager: Optional[AgentConfigManager] = None


def get_config_manager() -> AgentConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = AgentConfigManager()
    return _config_manager
