"""Media Machine Agent Role Definitions.

This module defines the 8 specialized agent roles that mirror a professional newsroom:

1. Research Agent ("The Scout") - Find and gather raw information
2. Editor Agent ("The Curator") - Decide what's newsworthy
3. Writer Agent ("The Voice") - Transform stories into engaging scripts
4. Fact-Checker Agent ("The Verifier") - Verify claims and accuracy
5. Localization Agent ("The Adapter") - Adapt for languages and cultures
6. Producer Agent ("The Director") - Orchestrate video production
7. Social Media Agent ("The Promoter") - Distribute across platforms
8. Analytics Agent ("The Analyst") - Track performance and feedback
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from .config import AgentConfig, AgentType, LLMConfig, ANALYTICAL_LLM_CONFIG, DEFAULT_LLM_CONFIG, CREATIVE_LLM_CONFIG


class AgentRole(str, Enum):
    """The 8 professional media roles."""
    RESEARCH = "research"
    EDITOR = "editor"
    WRITER = "writer"
    FACT_CHECKER = "fact_checker"
    LOCALIZATION = "localization"
    PRODUCER = "producer"
    SOCIAL_MEDIA = "social_media"
    ANALYTICS = "analytics"


# =============================================================================
# ROLE METADATA
# =============================================================================

ROLE_METADATA: Dict[AgentRole, Dict[str, Any]] = {
    AgentRole.RESEARCH: {
        "name": "Research Agent",
        "nickname": "The Scout",
        "description": "Find and gather raw information from multiple sources",
        "responsibilities": [
            "Monitor configured news sources (RSS, Telegram, Nitter)",
            "Extract and normalize article data",
            "Initial relevance scoring for Malaysian business context",
            "Detect breaking news vs evergreen content",
            "Flag potential duplicates across sources",
        ],
        "inputs": ["source_configs", "date_range", "topic_filters"],
        "outputs": ["raw_articles", "source_metadata"],
        "tools": ["rss_fetcher", "telegram_client", "nitter_scraper", "relevance_scorer"],
        "requires_llm": False,
    },

    AgentRole.EDITOR: {
        "name": "Editor Agent",
        "nickname": "The Curator",
        "description": "The editorial brain - decides what matters for Malaysian SMEs",
        "responsibilities": [
            "Deduplicate semantically similar articles",
            "Score newsworthiness for target audience (Malaysian SME owners)",
            "Categorize into segments (Local, Business, AI/Tech)",
            "Decide story priority and ordering",
            "Identify the 'so what' angle for each story",
            "Flag stories that need fact-checking",
        ],
        "inputs": ["raw_articles", "audience_profile", "content_pillars"],
        "outputs": ["selected_stories", "segment_assignments", "editorial_angles", "stories_needing_verification"],
        "tools": ["semantic_deduplicator", "relevance_ranker", "topic_classifier", "angle_generator"],
        "requires_llm": True,
    },

    AgentRole.WRITER: {
        "name": "Writer Agent",
        "nickname": "The Voice",
        "description": "Writes in Maya's distinctive voice with practical SME focus",
        "responsibilities": [
            "Generate segment scripts in Maya's voice",
            "Apply language config (en-SG code-switching, ms-MY, etc.)",
            "Ensure practical 'what to do' angle in every story",
            "Write hooks, transitions, and closings",
            "Maintain consistent tone across segments",
            "Target word count for video duration",
        ],
        "inputs": ["selected_stories", "editorial_angles", "language_config", "segment_type", "target_duration"],
        "outputs": ["script", "word_count", "estimated_duration"],
        "tools": ["script_generator", "tone_checker", "duration_estimator"],
        "requires_llm": True,
    },

    AgentRole.FACT_CHECKER: {
        "name": "Fact-Checker Agent",
        "nickname": "The Verifier",
        "description": "Ensures accuracy before publishing",
        "responsibilities": [
            "Verify statistics and numbers cited in scripts",
            "Check that attributions are accurate",
            "Cross-reference claims with original sources",
            "Flag unverifiable claims for removal or softening",
            "Ensure regulatory/policy information is current",
            "Check company names, titles, and proper nouns",
        ],
        "inputs": ["scripts", "source_articles", "claims_to_verify"],
        "outputs": ["verification_report", "flagged_claims", "suggested_corrections", "confidence_score"],
        "tools": ["web_search", "source_validator", "claim_extractor"],
        "requires_llm": True,
    },

    AgentRole.LOCALIZATION: {
        "name": "Localization Agent",
        "nickname": "The Adapter",
        "description": "Adapts content for different languages and cultural contexts",
        "responsibilities": [
            "Translate scripts between languages (EN ↔ BM ↔ ZH)",
            "Adapt cultural references appropriately",
            "Ensure code-switching feels natural in target language",
            "Localize examples (RM amounts, local business types)",
            "Flag content that doesn't translate well",
            "Maintain Maya's voice across languages",
        ],
        "inputs": ["source_script", "source_language", "target_language", "language_config"],
        "outputs": ["localized_script", "adaptation_notes", "untranslatable_segments", "requires_native_review"],
        "tools": ["translator", "cultural_adapter", "code_switch_naturalizer"],
        "requires_llm": True,
    },

    AgentRole.PRODUCER: {
        "name": "Producer Agent",
        "nickname": "The Director",
        "description": "Orchestrates video production with HeyGen",
        "responsibilities": [
            "Select appropriate avatar and voice for language",
            "Configure HeyGen video parameters",
            "Manage video generation queue",
            "Handle video status polling and retrieval",
            "Add B-roll, graphics, lower-thirds (future)",
            "Ensure video meets platform specs (9:16, duration, etc.)",
        ],
        "inputs": ["approved_script", "language_config", "avatar_config", "video_specs"],
        "outputs": ["video_url", "video_metadata", "thumbnail", "duration_actual"],
        "tools": ["heygen_client", "video_validator", "thumbnail_generator"],
        "requires_llm": False,
    },

    AgentRole.SOCIAL_MEDIA: {
        "name": "Social Media Agent",
        "nickname": "The Promoter",
        "description": "Handles platform-specific adaptation and distribution",
        "responsibilities": [
            "Generate platform-specific captions",
            "Select hashtags by platform and language",
            "Adapt video format if needed (duration cuts for TikTok)",
            "Schedule posts for optimal timing",
            "Handle Blotato API integration",
            "Create WhatsApp broadcast content",
            "Generate YouTube descriptions and tags",
        ],
        "inputs": ["video_url", "script_summary", "target_platforms", "language_config", "scheduling_preferences"],
        "outputs": ["platform_posts", "post_ids", "scheduled_times"],
        "tools": ["blotato_client", "whatsapp_broadcaster", "caption_generator", "hashtag_optimizer"],
        "requires_llm": True,
    },

    AgentRole.ANALYTICS: {
        "name": "Analytics Agent",
        "nickname": "The Analyst",
        "description": "Tracks performance and feeds insights back into the system",
        "responsibilities": [
            "Track engagement metrics across platforms",
            "Identify top-performing content patterns",
            "Analyze audience demographics and behavior",
            "Generate weekly performance reports",
            "Recommend topic adjustments based on data",
            "Track lead attribution (content → ErzyCall signup)",
        ],
        "inputs": ["post_ids", "date_range", "content_metadata"],
        "outputs": ["performance_report", "top_performers", "recommendations", "lead_attribution"],
        "tools": ["platform_analytics_apis", "report_generator", "trend_analyzer"],
        "requires_llm": True,
    },
}


# =============================================================================
# AGENT CONFIGURATIONS
# =============================================================================

MEDIA_MACHINE_AGENTS: Dict[str, AgentConfig] = {
    # 1. RESEARCH AGENT - The Scout
    "research": AgentConfig(
        id="research",
        name="Research Agent",
        description="Find and gather raw information from multiple sources",
        agent_type=AgentType.AGGREGATOR,
        timeout_seconds=180,
        params={
            "lookback_days": 7,
            "sources": ["rss", "telegram", "twitter"],
            "min_articles": 20,
            "max_articles": 200,
        },
        output_field="raw_articles",
    ),

    # 2. EDITOR AGENT - The Curator
    "editor": AgentConfig(
        id="editor",
        name="Editor Agent",
        description="The editorial brain - decides what matters for Malaysian SMEs",
        agent_type=AgentType.ANALYZER,
        llm_config=ANALYTICAL_LLM_CONFIG,
        timeout_seconds=300,
        max_items=100,
        params={
            "deduplication_threshold": 0.85,
            "min_relevance_score": 0.3,
            "max_stories_per_segment": 15,
            "segments": ["local", "business", "ai_tech"],
        },
        depends_on=["research"],
        output_field="selected_stories",
    ),

    # 3. WRITER AGENTS - The Voice (one per segment)
    "writer_local": AgentConfig(
        id="writer_local",
        name="Writer Agent (Local News)",
        description="Writes local & international news in Maya's voice",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,
        params={
            "segment": "local",
            "target_duration_seconds": 60,
            "target_word_count": 150,
        },
        depends_on=["editor"],
        output_field="local_script",
    ),

    "writer_business": AgentConfig(
        id="writer_business",
        name="Writer Agent (Business News)",
        description="Writes business news in Maya's voice",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,
        params={
            "segment": "business",
            "target_duration_seconds": 50,
            "target_word_count": 130,
        },
        depends_on=["editor"],
        output_field="business_script",
    ),

    "writer_ai": AgentConfig(
        id="writer_ai",
        name="Writer Agent (AI & Tech)",
        description="Writes AI & tech news in Maya's voice",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=120,
        max_items=10,
        params={
            "segment": "ai_tech",
            "target_duration_seconds": 50,
            "target_word_count": 130,
        },
        depends_on=["editor"],
        output_field="ai_script",
    ),

    # 4. FACT-CHECKER AGENT - The Verifier
    "fact_checker": AgentConfig(
        id="fact_checker",
        name="Fact-Checker Agent",
        description="Verifies claims, statistics, and attributions",
        agent_type=AgentType.ANALYZER,
        llm_config=ANALYTICAL_LLM_CONFIG,
        timeout_seconds=180,
        params={
            "verify_statistics": True,
            "verify_attributions": True,
            "verify_company_names": True,
            "confidence_threshold": 0.8,
        },
        depends_on=["writer_local", "writer_business", "writer_ai"],
        output_field="verification_report",
    ),

    # 5. SCRIPT ASSEMBLER - Combines verified scripts
    "script_assembler": AgentConfig(
        id="script_assembler",
        name="Script Assembler",
        description="Combines segment scripts with intro/outro",
        agent_type=AgentType.PROCESSOR,
        llm_config=DEFAULT_LLM_CONFIG,
        timeout_seconds=60,
        depends_on=["fact_checker"],
        output_field="full_script",
    ),

    # 6. LOCALIZATION AGENT - The Adapter
    "localization": AgentConfig(
        id="localization",
        name="Localization Agent",
        description="Adapts content for different languages and cultures",
        agent_type=AgentType.SYNTHESIZER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=180,
        params={
            "maintain_code_switching": True,
            "localize_examples": True,
            "preserve_voice": True,
        },
        depends_on=["script_assembler"],
        output_field="localized_scripts",
    ),

    # 7. QUALITY CONTROL GATE - Human approval
    "quality_control": AgentConfig(
        id="quality_control",
        name="Quality Control Gate",
        description="Human approval checkpoint for scripts",
        agent_type=AgentType.GATE,
        timeout_seconds=86400,  # 24 hours
        depends_on=["localization"],
        params={
            "notification_channels": ["slack", "telegram"],
            "require_feedback_on_reject": True,
            "auto_approve_after_hours": None,
        },
    ),

    # 8. PRODUCER AGENT - The Director
    "producer": AgentConfig(
        id="producer",
        name="Producer Agent",
        description="Orchestrates video production with HeyGen",
        agent_type=AgentType.PUBLISHER,
        timeout_seconds=900,  # 15 minutes for video generation
        depends_on=["quality_control"],
        params={
            "aspect_ratio": "9:16",
            "background_color": "#1a1a2e",
            "max_wait_seconds": 600,
            "generate_thumbnail": True,
        },
        output_field="video_url",
    ),

    # 9. VIDEO APPROVAL GATE
    "video_approval": AgentConfig(
        id="video_approval",
        name="Video Approval Gate",
        description="Human approval checkpoint for video",
        agent_type=AgentType.GATE,
        timeout_seconds=86400,
        depends_on=["producer"],
        params={
            "notification_channels": ["slack", "telegram"],
        },
    ),

    # 10. SOCIAL MEDIA AGENT - The Promoter
    "social_media": AgentConfig(
        id="social_media",
        name="Social Media Agent",
        description="Distributes content across platforms",
        agent_type=AgentType.PUBLISHER,
        llm_config=CREATIVE_LLM_CONFIG,
        timeout_seconds=300,
        depends_on=["video_approval"],
        params={
            "platforms": ["instagram", "tiktok", "youtube", "linkedin"],
            "generate_platform_captions": True,
            "optimize_hashtags": True,
            "schedule_delay_minutes": 0,
        },
        output_field="post_results",
    ),

    # 11. ANALYTICS AGENT - The Analyst
    "analytics": AgentConfig(
        id="analytics",
        name="Analytics Agent",
        description="Tracks performance and provides feedback",
        agent_type=AgentType.ANALYZER,
        llm_config=ANALYTICAL_LLM_CONFIG,
        timeout_seconds=120,
        depends_on=["social_media"],
        params={
            "track_engagement": True,
            "generate_report": True,
            "identify_patterns": True,
        },
        output_field="analytics_report",
    ),
}


# =============================================================================
# MEDIA MACHINE PIPELINE FLOW
# =============================================================================

MEDIA_MACHINE_FLOW = [
    # Phase 1: Research & Curation
    "research",
    "editor",

    # Phase 2: Content Creation (Writers run in parallel)
    ["writer_local", "writer_business", "writer_ai"],

    # Phase 3: Quality Assurance
    "fact_checker",
    "script_assembler",
    "localization",

    # Phase 4: Human Approval
    "quality_control",

    # Phase 5: Production
    "producer",
    "video_approval",

    # Phase 6: Distribution & Analysis
    "social_media",
    "analytics",
]

MEDIA_MACHINE_INTERRUPTS = ["quality_control", "video_approval"]

MEDIA_MACHINE_CONDITIONAL_ROUTES = {
    "quality_control": {
        "approved": "producer",
        "revise": "writer_local",  # Loop back to rewrite
        "reject": "__end__",
    },
    "video_approval": {
        "approved": "social_media",
        "revise": "producer",  # Regenerate video
        "reject": "__end__",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_role_metadata(role: AgentRole) -> Dict[str, Any]:
    """Get metadata for a specific role."""
    return ROLE_METADATA.get(role, {})


def get_role_by_agent_id(agent_id: str) -> Optional[AgentRole]:
    """Map an agent ID to its role."""
    role_mapping = {
        "research": AgentRole.RESEARCH,
        "editor": AgentRole.EDITOR,
        "writer_local": AgentRole.WRITER,
        "writer_business": AgentRole.WRITER,
        "writer_ai": AgentRole.WRITER,
        "fact_checker": AgentRole.FACT_CHECKER,
        "localization": AgentRole.LOCALIZATION,
        "producer": AgentRole.PRODUCER,
        "social_media": AgentRole.SOCIAL_MEDIA,
        "analytics": AgentRole.ANALYTICS,
    }
    return role_mapping.get(agent_id)


def get_agents_by_role(role: AgentRole) -> List[AgentConfig]:
    """Get all agent configs for a specific role."""
    agents = []
    for agent_id, config in MEDIA_MACHINE_AGENTS.items():
        if get_role_by_agent_id(agent_id) == role:
            agents.append(config)
    return agents


def list_all_roles() -> List[Dict[str, Any]]:
    """List all roles with their metadata."""
    return [
        {
            "role": role.value,
            **metadata,
        }
        for role, metadata in ROLE_METADATA.items()
    ]
