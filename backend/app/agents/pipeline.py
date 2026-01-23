"""Main LangGraph pipeline for Maya AI News Anchor."""

from typing import Optional, Dict, Any
from datetime import date

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.schemas import PipelineStatus
from app.services.database import get_db_service
from app.services.notification import get_notification_service
from .state import MayaState, create_initial_state
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


class MayaPipeline:
    """Maya AI News Anchor pipeline orchestrator."""

    def __init__(self):
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        builder = StateGraph(MayaState)

        # Add nodes
        builder.add_node("aggregate", aggregate_news)
        builder.add_node("deduplicate", deduplicate_articles)
        builder.add_node("categorize", categorize_articles)
        builder.add_node("synthesize_local", synthesize_local)
        builder.add_node("synthesize_business", synthesize_business)
        builder.add_node("synthesize_ai", synthesize_ai)
        builder.add_node("generate_scripts", generate_scripts)
        builder.add_node("script_approval", script_approval_gate)
        builder.add_node("generate_video", generate_video)
        builder.add_node("video_approval", video_approval_gate)
        builder.add_node("publish", publish_to_social)

        # Define edges
        builder.add_edge(START, "aggregate")
        builder.add_edge("aggregate", "deduplicate")
        builder.add_edge("deduplicate", "categorize")

        # Parallel synthesis - fan out
        builder.add_edge("categorize", "synthesize_local")
        builder.add_edge("categorize", "synthesize_business")
        builder.add_edge("categorize", "synthesize_ai")

        # Fan in to generate scripts (needs all three)
        builder.add_edge("synthesize_local", "generate_scripts")
        builder.add_edge("synthesize_business", "generate_scripts")
        builder.add_edge("synthesize_ai", "generate_scripts")

        builder.add_edge("generate_scripts", "script_approval")

        # After script approval, continue to video
        builder.add_conditional_edges(
            "script_approval",
            self._route_after_script_approval,
            {
                "generate_video": "generate_video",
                "end": END,
            }
        )

        builder.add_edge("generate_video", "video_approval")

        # After video approval, continue to publish
        builder.add_conditional_edges(
            "video_approval",
            self._route_after_video_approval,
            {
                "publish": "publish",
                "end": END,
            }
        )

        builder.add_edge("publish", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _route_after_script_approval(self, state: MayaState) -> str:
        """Route after script approval gate."""
        if state.get("script_approved"):
            return "generate_video"
        if state.get("error"):
            return "end"
        # If not approved, wait (this will be handled by interrupt)
        return "generate_video"  # Default to continue

    def _route_after_video_approval(self, state: MayaState) -> str:
        """Route after video approval gate."""
        if state.get("video_approved"):
            return "publish"
        if state.get("error"):
            return "end"
        return "publish"  # Default to continue

    async def start_briefing(
        self,
        week_number: Optional[int] = None,
        year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Start a new weekly briefing pipeline."""
        today = date.today()
        week_number = week_number or today.isocalendar()[1]
        year = year or today.year

        initial_state = create_initial_state(week_number, year)
        thread_id = initial_state["thread_id"]

        config = {"configurable": {"thread_id": thread_id}}

        # Create database record
        db = get_db_service()
        from app.models.schemas import WeeklyBriefingCreate
        await db.create_briefing(WeeklyBriefingCreate(
            year=year,
            week_number=week_number,
        ))

        # Run the pipeline up to the first approval gate
        result = await self.graph.ainvoke(initial_state, config=config)

        return {
            "thread_id": thread_id,
            "status": result.get("status", PipelineStatus.AGGREGATING).value,
            "week_number": week_number,
            "year": year,
        }

    async def approve_script(
        self,
        thread_id: str,
        approved: bool,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle script approval and continue pipeline."""
        config = {"configurable": {"thread_id": thread_id}}

        # Update state with approval
        update = {
            "script_approved": approved,
            "script_feedback": feedback,
            "status": PipelineStatus.GENERATING_VIDEO if approved else PipelineStatus.FAILED,
        }

        if not approved:
            update["error"] = feedback or "Script rejected"

        # Resume the pipeline
        result = await self.graph.ainvoke(update, config=config)

        # Update database
        db = get_db_service()
        briefing = await db.get_briefing_by_thread(thread_id)
        if briefing:
            from app.models.schemas import WeeklyBriefingUpdate
            from datetime import datetime
            await db.update_briefing(
                briefing.id,
                WeeklyBriefingUpdate(
                    local_script=result.get("local_script"),
                    business_script=result.get("business_script"),
                    ai_script=result.get("ai_script"),
                    full_script=result.get("full_script"),
                    script_approved_at=datetime.utcnow() if approved else None,
                    status=PipelineStatus(result.get("status", PipelineStatus.GENERATING_VIDEO)),
                )
            )

        return {
            "thread_id": thread_id,
            "status": result.get("status", PipelineStatus.GENERATING_VIDEO).value,
            "approved": approved,
        }

    async def approve_video(
        self,
        thread_id: str,
        approved: bool,
    ) -> Dict[str, Any]:
        """Handle video approval and continue to publishing."""
        config = {"configurable": {"thread_id": thread_id}}

        update = {
            "video_approved": approved,
            "status": PipelineStatus.PUBLISHING if approved else PipelineStatus.FAILED,
        }

        if not approved:
            update["error"] = "Video rejected"

        # Resume the pipeline
        result = await self.graph.ainvoke(update, config=config)

        # Update database
        db = get_db_service()
        briefing = await db.get_briefing_by_thread(thread_id)
        if briefing:
            from app.models.schemas import WeeklyBriefingUpdate
            from datetime import datetime
            await db.update_briefing(
                briefing.id,
                WeeklyBriefingUpdate(
                    video_approved_at=datetime.utcnow() if approved else None,
                    published_at=datetime.utcnow() if result.get("status") == PipelineStatus.COMPLETED else None,
                    status=PipelineStatus(result.get("status", PipelineStatus.COMPLETED)),
                )
            )

        return {
            "thread_id": thread_id,
            "status": result.get("status", PipelineStatus.COMPLETED).value,
            "approved": approved,
            "post_results": result.get("post_results"),
        }

    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current state for a thread."""
        config = {"configurable": {"thread_id": thread_id}}

        try:
            state = await self.graph.aget_state(config)
            if state and state.values:
                return dict(state.values)
        except Exception:
            pass

        return None

    async def get_history(self, thread_id: str) -> list:
        """Get state history for a thread."""
        config = {"configurable": {"thread_id": thread_id}}

        history = []
        async for state in self.graph.aget_state_history(config):
            history.append({
                "values": dict(state.values) if state.values else {},
                "next": list(state.next) if state.next else [],
            })

        return history


# Singleton
_pipeline: Optional[MayaPipeline] = None


def get_pipeline() -> MayaPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MayaPipeline()
    return _pipeline
