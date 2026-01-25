"""Persistent configuration storage for agent settings.

This module provides database-backed storage for agent configurations,
enabling persistence across restarts and configuration versioning.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging

from ..core.database import supabase
from .config import (
    AgentConfig,
    SegmentConfig,
    LLMConfig,
    PipelineFlowConfig,
    DEFAULT_AGENTS,
    DEFAULT_SEGMENTS,
    DEFAULT_PIPELINE_FLOW,
)

logger = logging.getLogger(__name__)


class ConfigStore:
    """Database-backed configuration storage."""

    TABLE_NAME = "agent_configs"

    async def initialize_tables(self) -> None:
        """Ensure configuration tables exist."""
        # The table should be created via schema.sql
        # This is just a check
        try:
            result = supabase.table(self.TABLE_NAME).select("id").limit(1).execute()
            logger.info("Agent config table exists")
        except Exception as e:
            logger.warning(f"Agent config table may not exist: {e}")

    # -------------------------------------------------------------------------
    # Agent Configuration
    # -------------------------------------------------------------------------

    async def save_agent_config(
        self,
        agent_id: str,
        config: AgentConfig,
        version_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save agent configuration to database."""
        data = {
            "config_type": "agent",
            "config_id": agent_id,
            "config_data": config.model_dump(),
            "version_note": version_note,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table(self.TABLE_NAME).upsert(
            data,
            on_conflict="config_type,config_id"
        ).execute()

        return result.data[0] if result.data else data

    async def load_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration from database."""
        result = supabase.table(self.TABLE_NAME).select("*").eq(
            "config_type", "agent"
        ).eq(
            "config_id", agent_id
        ).execute()

        if result.data:
            config_data = result.data[0]["config_data"]
            return AgentConfig(**config_data)
        return None

    async def load_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """Load all agent configurations from database."""
        result = supabase.table(self.TABLE_NAME).select("*").eq(
            "config_type", "agent"
        ).execute()

        configs = {}
        for row in result.data:
            agent_id = row["config_id"]
            configs[agent_id] = AgentConfig(**row["config_data"])

        return configs

    async def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration from database."""
        result = supabase.table(self.TABLE_NAME).delete().eq(
            "config_type", "agent"
        ).eq(
            "config_id", agent_id
        ).execute()

        return len(result.data) > 0

    # -------------------------------------------------------------------------
    # Segment Configuration
    # -------------------------------------------------------------------------

    async def save_segment_config(
        self,
        segment_id: str,
        config: SegmentConfig,
    ) -> Dict[str, Any]:
        """Save segment configuration to database."""
        data = {
            "config_type": "segment",
            "config_id": segment_id,
            "config_data": config.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table(self.TABLE_NAME).upsert(
            data,
            on_conflict="config_type,config_id"
        ).execute()

        return result.data[0] if result.data else data

    async def load_all_segment_configs(self) -> Dict[str, SegmentConfig]:
        """Load all segment configurations from database."""
        result = supabase.table(self.TABLE_NAME).select("*").eq(
            "config_type", "segment"
        ).execute()

        configs = {}
        for row in result.data:
            segment_id = row["config_id"]
            configs[segment_id] = SegmentConfig(**row["config_data"])

        return configs

    # -------------------------------------------------------------------------
    # Pipeline Flow Configuration
    # -------------------------------------------------------------------------

    async def save_pipeline_flow(self, config: PipelineFlowConfig) -> Dict[str, Any]:
        """Save pipeline flow configuration."""
        data = {
            "config_type": "pipeline_flow",
            "config_id": "default",
            "config_data": config.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
        }

        result = supabase.table(self.TABLE_NAME).upsert(
            data,
            on_conflict="config_type,config_id"
        ).execute()

        return result.data[0] if result.data else data

    async def load_pipeline_flow(self) -> Optional[PipelineFlowConfig]:
        """Load pipeline flow configuration."""
        result = supabase.table(self.TABLE_NAME).select("*").eq(
            "config_type", "pipeline_flow"
        ).eq(
            "config_id", "default"
        ).execute()

        if result.data:
            return PipelineFlowConfig(**result.data[0]["config_data"])
        return None

    # -------------------------------------------------------------------------
    # Full Configuration Export/Import
    # -------------------------------------------------------------------------

    async def export_all(self) -> Dict[str, Any]:
        """Export all configurations."""
        agents = await self.load_all_agent_configs()
        segments = await self.load_all_segment_configs()
        pipeline_flow = await self.load_pipeline_flow()

        return {
            "agents": {k: v.model_dump() for k, v in agents.items()},
            "segments": {k: v.model_dump() for k, v in segments.items()},
            "pipeline_flow": pipeline_flow.model_dump() if pipeline_flow else None,
            "exported_at": datetime.utcnow().isoformat(),
        }

    async def import_all(self, config: Dict[str, Any]) -> None:
        """Import all configurations."""
        if "agents" in config:
            for agent_id, agent_data in config["agents"].items():
                await self.save_agent_config(
                    agent_id,
                    AgentConfig(**agent_data),
                    version_note="Imported from backup"
                )

        if "segments" in config:
            for segment_id, segment_data in config["segments"].items():
                await self.save_segment_config(
                    segment_id,
                    SegmentConfig(**segment_data)
                )

        if "pipeline_flow" in config and config["pipeline_flow"]:
            await self.save_pipeline_flow(
                PipelineFlowConfig(**config["pipeline_flow"])
            )

    async def seed_defaults(self) -> None:
        """Seed database with default configurations if empty."""
        existing = await self.load_all_agent_configs()

        if not existing:
            logger.info("Seeding default agent configurations...")
            for agent_id, config in DEFAULT_AGENTS.items():
                await self.save_agent_config(agent_id, config, "Initial default")

            for segment_id, config in DEFAULT_SEGMENTS.items():
                await self.save_segment_config(segment_id, config)

            await self.save_pipeline_flow(DEFAULT_PIPELINE_FLOW)
            logger.info("Default configurations seeded")

    # -------------------------------------------------------------------------
    # Configuration History
    # -------------------------------------------------------------------------

    async def get_config_history(
        self,
        config_type: str,
        config_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get configuration change history."""
        result = supabase.table(f"{self.TABLE_NAME}_history").select("*").eq(
            "config_type", config_type
        ).eq(
            "config_id", config_id
        ).order(
            "created_at", desc=True
        ).limit(limit).execute()

        return result.data


# Global store instance
_config_store: Optional[ConfigStore] = None


def get_config_store() -> ConfigStore:
    """Get global config store instance."""
    global _config_store
    if _config_store is None:
        _config_store = ConfigStore()
    return _config_store
