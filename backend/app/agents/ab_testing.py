"""A/B testing support for agent configurations.

This module enables running experiments with different agent configurations,
tracking performance metrics, and making data-driven decisions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random
import hashlib
import logging

from pydantic import BaseModel, Field

from ..core.database import supabase
from .config import AgentConfig, LLMConfig

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Status of an A/B test experiment."""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantConfig(BaseModel):
    """Configuration for a test variant."""
    id: str
    name: str
    description: str = ""
    weight: float = 0.5  # Traffic allocation (0.0 to 1.0)

    # Agent overrides for this variant
    agent_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # LLM overrides (model, temperature, etc.)
    llm_overrides: Optional[Dict[str, Any]] = None


class Experiment(BaseModel):
    """An A/B test experiment."""
    id: str
    name: str
    description: str = ""
    status: ExperimentStatus = ExperimentStatus.DRAFT

    # Target agents for this experiment
    target_agents: List[str] = Field(default_factory=list)

    # Variants (including control)
    variants: List[VariantConfig] = Field(default_factory=list)

    # Metrics to track
    metrics: List[str] = Field(default_factory=lambda: [
        "execution_time_ms",
        "token_usage",
        "cost_usd",
        "error_rate",
    ])

    # Time bounds
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Sample size targets
    min_sample_per_variant: int = 100

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
    """Result record for an experiment execution."""
    experiment_id: str
    variant_id: str
    thread_id: str
    agent_id: str

    # Metrics
    execution_time_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    success: bool = True
    error_message: Optional[str] = None

    # Custom metrics
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ABTestingManager:
    """Manages A/B testing experiments."""

    EXPERIMENTS_TABLE = "ab_experiments"
    RESULTS_TABLE = "ab_experiment_results"

    def __init__(self):
        self._experiments: Dict[str, Experiment] = {}
        self._assignment_cache: Dict[str, str] = {}  # thread_id -> variant_id

    # -------------------------------------------------------------------------
    # Experiment Management
    # -------------------------------------------------------------------------

    async def create_experiment(self, experiment: Experiment) -> Experiment:
        """Create a new experiment."""
        # Validate weights sum to ~1.0
        total_weight = sum(v.weight for v in experiment.variants)
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")

        self._experiments[experiment.id] = experiment

        # Persist to database
        try:
            data = {
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "status": experiment.status.value,
                "config": experiment.model_dump(),
                "created_at": experiment.created_at.isoformat(),
            }
            supabase.table(self.EXPERIMENTS_TABLE).upsert(data).execute()
        except Exception as e:
            logger.warning(f"Failed to persist experiment: {e}")

        return experiment

    async def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        if experiment_id in self._experiments:
            return self._experiments[experiment_id]

        try:
            result = supabase.table(self.EXPERIMENTS_TABLE).select("*").eq(
                "id", experiment_id
            ).execute()

            if result.data:
                exp = Experiment(**result.data[0]["config"])
                self._experiments[experiment_id] = exp
                return exp
        except Exception as e:
            logger.warning(f"Failed to load experiment: {e}")

        return None

    async def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
    ) -> List[Experiment]:
        """List all experiments."""
        try:
            query = supabase.table(self.EXPERIMENTS_TABLE).select("*")
            if status:
                query = query.eq("status", status.value)
            result = query.execute()

            return [Experiment(**r["config"]) for r in result.data]
        except Exception:
            return list(self._experiments.values())

    async def start_experiment(self, experiment_id: str) -> Experiment:
        """Start an experiment."""
        exp = await self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        exp.status = ExperimentStatus.RUNNING
        exp.start_date = datetime.utcnow()

        try:
            supabase.table(self.EXPERIMENTS_TABLE).update({
                "status": exp.status.value,
                "config": exp.model_dump(),
            }).eq("id", experiment_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update experiment: {e}")

        return exp

    async def stop_experiment(self, experiment_id: str) -> Experiment:
        """Stop an experiment."""
        exp = await self.get_experiment(experiment_id)
        if not exp:
            raise ValueError(f"Experiment not found: {experiment_id}")

        exp.status = ExperimentStatus.COMPLETED
        exp.end_date = datetime.utcnow()

        try:
            supabase.table(self.EXPERIMENTS_TABLE).update({
                "status": exp.status.value,
                "config": exp.model_dump(),
            }).eq("id", experiment_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update experiment: {e}")

        return exp

    # -------------------------------------------------------------------------
    # Variant Assignment
    # -------------------------------------------------------------------------

    def assign_variant(
        self,
        experiment: Experiment,
        thread_id: str,
    ) -> VariantConfig:
        """Assign a variant to a thread (deterministic based on thread_id)."""
        cache_key = f"{experiment.id}:{thread_id}"

        if cache_key in self._assignment_cache:
            variant_id = self._assignment_cache[cache_key]
            for v in experiment.variants:
                if v.id == variant_id:
                    return v

        # Deterministic assignment using hash
        hash_input = f"{experiment.id}:{thread_id}".encode()
        hash_value = int(hashlib.sha256(hash_input).hexdigest(), 16)
        normalized = (hash_value % 10000) / 10000.0  # 0.0 to 1.0

        # Find variant based on cumulative weight
        cumulative = 0.0
        selected_variant = experiment.variants[0]

        for variant in experiment.variants:
            cumulative += variant.weight
            if normalized < cumulative:
                selected_variant = variant
                break

        self._assignment_cache[cache_key] = selected_variant.id
        return selected_variant

    def get_config_overrides(
        self,
        experiment: Experiment,
        variant: VariantConfig,
        agent_id: str,
    ) -> Dict[str, Any]:
        """Get configuration overrides for an agent in a variant."""
        overrides = {}

        # Apply agent-specific overrides
        if agent_id in variant.agent_overrides:
            overrides.update(variant.agent_overrides[agent_id])

        # Apply LLM overrides
        if variant.llm_overrides:
            overrides["llm_config"] = variant.llm_overrides

        return overrides

    # -------------------------------------------------------------------------
    # Result Recording
    # -------------------------------------------------------------------------

    async def record_result(self, result: ExperimentResult) -> None:
        """Record an experiment result."""
        try:
            data = {
                "experiment_id": result.experiment_id,
                "variant_id": result.variant_id,
                "thread_id": result.thread_id,
                "agent_id": result.agent_id,
                "execution_time_ms": result.execution_time_ms,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cost_usd": result.cost_usd,
                "success": result.success,
                "error_message": result.error_message,
                "custom_metrics": result.custom_metrics,
                "created_at": result.created_at.isoformat(),
            }
            supabase.table(self.RESULTS_TABLE).insert(data).execute()
        except Exception as e:
            logger.warning(f"Failed to record experiment result: {e}")

    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------

    async def get_experiment_results(
        self,
        experiment_id: str,
    ) -> Dict[str, Any]:
        """Get aggregated results for an experiment."""
        try:
            result = supabase.table(self.RESULTS_TABLE).select("*").eq(
                "experiment_id", experiment_id
            ).execute()

            records = result.data
        except Exception:
            return {"error": "Failed to load results"}

        if not records:
            return {"experiment_id": experiment_id, "message": "No results yet"}

        # Aggregate by variant
        by_variant = {}
        for record in records:
            variant_id = record["variant_id"]
            if variant_id not in by_variant:
                by_variant[variant_id] = {
                    "sample_size": 0,
                    "total_time_ms": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "successes": 0,
                    "failures": 0,
                }

            stats = by_variant[variant_id]
            stats["sample_size"] += 1
            stats["total_time_ms"] += record["execution_time_ms"]
            stats["total_tokens"] += record["input_tokens"] + record["output_tokens"]
            stats["total_cost"] += record["cost_usd"]
            if record["success"]:
                stats["successes"] += 1
            else:
                stats["failures"] += 1

        # Calculate averages
        for variant_id, stats in by_variant.items():
            n = stats["sample_size"]
            stats["avg_time_ms"] = round(stats["total_time_ms"] / n, 2) if n else 0
            stats["avg_tokens"] = round(stats["total_tokens"] / n, 2) if n else 0
            stats["avg_cost"] = round(stats["total_cost"] / n, 6) if n else 0
            stats["success_rate"] = round(stats["successes"] / n, 4) if n else 0
            stats["error_rate"] = round(stats["failures"] / n, 4) if n else 0

        # Calculate statistical significance (simplified)
        variants = list(by_variant.keys())
        significance = {}
        if len(variants) >= 2:
            control = by_variant[variants[0]]
            for variant_id in variants[1:]:
                treatment = by_variant[variant_id]

                # Simple effect size for cost
                if control["avg_cost"] > 0:
                    cost_diff_pct = (
                        (treatment["avg_cost"] - control["avg_cost"]) / control["avg_cost"]
                    ) * 100
                else:
                    cost_diff_pct = 0

                # Simple effect size for time
                if control["avg_time_ms"] > 0:
                    time_diff_pct = (
                        (treatment["avg_time_ms"] - control["avg_time_ms"]) / control["avg_time_ms"]
                    ) * 100
                else:
                    time_diff_pct = 0

                significance[variant_id] = {
                    "vs_control": variants[0],
                    "cost_diff_pct": round(cost_diff_pct, 2),
                    "time_diff_pct": round(time_diff_pct, 2),
                    "has_enough_samples": min(
                        control["sample_size"],
                        treatment["sample_size"]
                    ) >= 30,
                }

        return {
            "experiment_id": experiment_id,
            "total_samples": len(records),
            "by_variant": by_variant,
            "significance": significance,
        }


# Global manager instance
_ab_manager: Optional[ABTestingManager] = None


def get_ab_manager() -> ABTestingManager:
    """Get global A/B testing manager."""
    global _ab_manager
    if _ab_manager is None:
        _ab_manager = ABTestingManager()
    return _ab_manager


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_active_experiments_for_agent(agent_id: str) -> List[Experiment]:
    """Get all running experiments that target an agent."""
    manager = get_ab_manager()
    all_experiments = await manager.list_experiments(status=ExperimentStatus.RUNNING)

    return [
        exp for exp in all_experiments
        if agent_id in exp.target_agents or not exp.target_agents
    ]


def create_model_comparison_experiment(
    experiment_id: str,
    name: str,
    control_model: str = "gpt-4o",
    test_model: str = "gpt-4o-mini",
    target_agents: List[str] = None,
) -> Experiment:
    """Create a pre-configured experiment for comparing LLM models."""
    return Experiment(
        id=experiment_id,
        name=name,
        description=f"Compare {control_model} vs {test_model}",
        target_agents=target_agents or [],
        variants=[
            VariantConfig(
                id="control",
                name=f"Control ({control_model})",
                weight=0.5,
                llm_overrides={"model": control_model},
            ),
            VariantConfig(
                id="treatment",
                name=f"Treatment ({test_model})",
                weight=0.5,
                llm_overrides={"model": test_model},
            ),
        ],
    )


def create_temperature_experiment(
    experiment_id: str,
    name: str,
    temperatures: List[float] = None,
    target_agents: List[str] = None,
) -> Experiment:
    """Create an experiment for testing different temperature values."""
    temps = temperatures or [0.3, 0.7, 1.0]
    weight = 1.0 / len(temps)

    variants = [
        VariantConfig(
            id=f"temp_{int(t*10)}",
            name=f"Temperature {t}",
            weight=weight,
            llm_overrides={"temperature": t},
        )
        for t in temps
    ]

    return Experiment(
        id=experiment_id,
        name=name,
        description=f"Compare temperatures: {temps}",
        target_agents=target_agents or [],
        variants=variants,
    )
