"""Cost tracking for LLM usage per agent.

This module tracks token usage and estimated costs for each agent,
enabling cost monitoring, budgeting, and optimization.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from ..core.database import supabase

logger = logging.getLogger(__name__)


# Pricing per 1M tokens (as of 2024, approximate)
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
}


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __post_init__(self):
        if self.total_tokens == 0:
            self.total_tokens = self.input_tokens + self.output_tokens


@dataclass
class CostRecord:
    """Cost record for a single agent execution."""
    agent_id: str
    thread_id: str
    model: str
    usage: TokenUsage
    estimated_cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CostTracker:
    """Tracks LLM costs per agent and pipeline."""

    TABLE_NAME = "agent_cost_logs"

    def __init__(self):
        self._session_costs: Dict[str, List[CostRecord]] = {}

    def calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """Calculate estimated cost in USD for token usage."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o"])

        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]

        return round(input_cost + output_cost, 6)

    async def log_usage(
        self,
        agent_id: str,
        thread_id: str,
        model: str,
        usage: TokenUsage,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostRecord:
        """Log token usage for an agent execution."""
        cost = self.calculate_cost(model, usage)

        record = CostRecord(
            agent_id=agent_id,
            thread_id=thread_id,
            model=model,
            usage=usage,
            estimated_cost_usd=cost,
            metadata=metadata or {},
        )

        # Store in session memory
        if thread_id not in self._session_costs:
            self._session_costs[thread_id] = []
        self._session_costs[thread_id].append(record)

        # Persist to database
        try:
            data = {
                "agent_id": agent_id,
                "thread_id": thread_id,
                "model": model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "estimated_cost_usd": cost,
                "metadata": metadata or {},
                "created_at": record.timestamp.isoformat(),
            }
            supabase.table(self.TABLE_NAME).insert(data).execute()
        except Exception as e:
            logger.warning(f"Failed to persist cost log: {e}")

        return record

    async def get_thread_costs(self, thread_id: str) -> Dict[str, Any]:
        """Get total costs for a pipeline thread."""
        try:
            result = supabase.table(self.TABLE_NAME).select("*").eq(
                "thread_id", thread_id
            ).execute()

            records = result.data
        except Exception:
            # Fall back to session memory
            records = [
                {
                    "agent_id": r.agent_id,
                    "model": r.model,
                    "input_tokens": r.usage.input_tokens,
                    "output_tokens": r.usage.output_tokens,
                    "total_tokens": r.usage.total_tokens,
                    "estimated_cost_usd": r.estimated_cost_usd,
                }
                for r in self._session_costs.get(thread_id, [])
            ]

        # Aggregate by agent
        by_agent = {}
        total_cost = 0.0
        total_tokens = 0

        for record in records:
            agent_id = record["agent_id"]
            if agent_id not in by_agent:
                by_agent[agent_id] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                }

            by_agent[agent_id]["calls"] += 1
            by_agent[agent_id]["input_tokens"] += record["input_tokens"]
            by_agent[agent_id]["output_tokens"] += record["output_tokens"]
            by_agent[agent_id]["total_tokens"] += record["total_tokens"]
            by_agent[agent_id]["cost_usd"] += record["estimated_cost_usd"]

            total_cost += record["estimated_cost_usd"]
            total_tokens += record["total_tokens"]

        return {
            "thread_id": thread_id,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "by_agent": by_agent,
        }

    async def get_agent_costs(
        self,
        agent_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get cost summary for an agent over a time period."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            result = supabase.table(self.TABLE_NAME).select("*").eq(
                "agent_id", agent_id
            ).gte(
                "created_at", since
            ).execute()

            records = result.data
        except Exception:
            records = []

        total_cost = sum(r["estimated_cost_usd"] for r in records)
        total_tokens = sum(r["total_tokens"] for r in records)

        # Group by model
        by_model = {}
        for record in records:
            model = record["model"]
            if model not in by_model:
                by_model[model] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += record["total_tokens"]
            by_model[model]["cost_usd"] += record["estimated_cost_usd"]

        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_calls": len(records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_model": by_model,
            "avg_cost_per_call": round(total_cost / len(records), 4) if records else 0,
        }

    async def get_daily_costs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily cost breakdown."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            result = supabase.table(self.TABLE_NAME).select("*").gte(
                "created_at", since
            ).order("created_at").execute()

            records = result.data
        except Exception:
            return []

        # Group by date
        by_date = {}
        for record in records:
            date = record["created_at"][:10]  # YYYY-MM-DD
            if date not in by_date:
                by_date[date] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            by_date[date]["calls"] += 1
            by_date[date]["tokens"] += record["total_tokens"]
            by_date[date]["cost_usd"] += record["estimated_cost_usd"]

        return [
            {"date": date, **stats}
            for date, stats in sorted(by_date.items())
        ]

    async def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get overall cost summary."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        try:
            result = supabase.table(self.TABLE_NAME).select("*").gte(
                "created_at", since
            ).execute()

            records = result.data
        except Exception:
            records = []

        total_cost = sum(r["estimated_cost_usd"] for r in records)
        total_tokens = sum(r["total_tokens"] for r in records)

        # Top agents by cost
        by_agent = {}
        for record in records:
            agent_id = record["agent_id"]
            if agent_id not in by_agent:
                by_agent[agent_id] = 0.0
            by_agent[agent_id] += record["estimated_cost_usd"]

        top_agents = sorted(
            [{"agent_id": k, "cost_usd": round(v, 4)} for k, v in by_agent.items()],
            key=lambda x: x["cost_usd"],
            reverse=True,
        )[:5]

        return {
            "period_days": days,
            "total_calls": len(records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_daily_cost": round(total_cost / days, 4) if days > 0 else 0,
            "top_agents_by_cost": top_agents,
        }


# Global tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


# =============================================================================
# CALLBACK WRAPPER FOR LLM
# =============================================================================

class CostTrackingCallback:
    """Callback to track LLM costs automatically."""

    def __init__(self, agent_id: str, thread_id: str, model: str):
        self.agent_id = agent_id
        self.thread_id = thread_id
        self.model = model
        self.tracker = get_cost_tracker()

    async def on_llm_end(self, response: Any) -> None:
        """Called when LLM completes. Extract usage and log."""
        try:
            # Try to extract usage from response
            usage_data = getattr(response, "usage_metadata", None)
            if usage_data:
                usage = TokenUsage(
                    input_tokens=usage_data.get("input_tokens", 0),
                    output_tokens=usage_data.get("output_tokens", 0),
                )
                await self.tracker.log_usage(
                    self.agent_id,
                    self.thread_id,
                    self.model,
                    usage,
                )
        except Exception as e:
            logger.warning(f"Failed to track LLM cost: {e}")
