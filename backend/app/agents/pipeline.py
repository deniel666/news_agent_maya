"""FPF-Compliant LangGraph Pipeline for Maya AI News Anchor.

Implements:
- Pattern A.1.1: Bounded Contexts (Fact Extraction vs Persona Projection)
- Pattern A.10: Evidence Graph (provenance tracking)
- Pattern A.15: Work vs Method Description (draft vs approved)
- Pattern E.9: Structured HITL (Design Rationale Records)
- Pattern F.9: Brand Bridge (promotional opportunities)

Graph Flow:
    START
      │
      ▼
    aggregate_news
      │
      ▼
    deduplicate
      │
      ▼
    categorize
      │
      ▼
    bridge_selector ─────────────────┐
      │                              │
      ▼                              ▼
    ┌─────────────────────────────────────────┐
    │     FACT EXTRACTION (Parallel)          │
    │  ┌─────────┬─────────┬─────────┐        │
    │  │ local   │business │ ai_tech │        │
    │  └────┬────┴────┬────┴────┬────┘        │
    │       └─────────┼─────────┘             │
    └─────────────────┼───────────────────────┘
                      ▼
    ┌─────────────────────────────────────────┐
    │     PERSONA PROJECTION (Parallel)       │
    │  ┌─────────┬─────────┬─────────┐        │
    │  │ local   │business │ ai_tech │        │
    │  └────┬────┴────┬────┴────┬────┘        │
    │       └─────────┼─────────┘             │
    └─────────────────┼───────────────────────┘
                      ▼
               compile_script
                      │
                      ▼
               script_review ◄───── HITL Gate #1
                      │
              ┌───────┴───────┐
              │ approved?     │
              ▼               ▼
         generate_video    revise_script (loop)
              │
              ▼
         video_review ◄───── HITL Gate #2
              │
              ▼
           publish
              │
              ▼
             END
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.schemas import PipelineStatus
from app.services.database import get_db_service
from app.services.notification import get_notification_service
from .state import (
    MayaState,
    create_initial_state,
    DesignRationaleRecord,
    RejectionCategory,
    ScriptVersion,
)
from .nodes import (
    # Evidence Layer
    aggregate_news,
    deduplicate_articles,
    categorize_articles,
    # Bridge Layer
    detect_bridge_opportunities,
    select_best_bridge,
    # Fact Extraction Layer (Bounded Context: Journalism)
    extract_local_facts,
    extract_business_facts,
    extract_ai_facts,
    # Persona Projection Layer (Bounded Context: Maya)
    project_local_persona,
    project_business_persona,
    project_ai_persona,
    # Script Compilation
    compile_full_script,
    revise_script,
    # Approval Gates
    script_review_gate,
    video_review_gate,
    # Video & Publishing
    generate_video,
    publish_to_social,
)


class MayaPipeline:
    """FPF-Compliant Maya AI News Anchor pipeline orchestrator."""

    def __init__(self):
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the FPF-compliant LangGraph workflow."""
        builder = StateGraph(MayaState)

        # =================================================================
        # NODE DEFINITIONS
        # =================================================================

        # Evidence Layer
        builder.add_node("aggregate", aggregate_news)
        builder.add_node("deduplicate", deduplicate_articles)
        builder.add_node("categorize", categorize_articles)

        # Bridge Layer (Pattern F.9)
        builder.add_node("detect_bridges", detect_bridge_opportunities)
        builder.add_node("select_bridge", select_best_bridge)

        # Fact Extraction Layer (Pattern A.1.1 - Journalism Context)
        builder.add_node("extract_local_facts", extract_local_facts)
        builder.add_node("extract_business_facts", extract_business_facts)
        builder.add_node("extract_ai_facts", extract_ai_facts)

        # Persona Projection Layer (Pattern A.1.1 - Maya Context)
        builder.add_node("project_local", project_local_persona)
        builder.add_node("project_business", project_business_persona)
        builder.add_node("project_ai", project_ai_persona)

        # Script Compilation (Pattern A.15)
        builder.add_node("compile_script", compile_full_script)
        builder.add_node("revise_script", revise_script)

        # HITL Gates (Pattern E.9)
        builder.add_node("script_review", script_review_gate)
        builder.add_node("video_review", video_review_gate)

        # Video & Publishing
        builder.add_node("generate_video", generate_video)
        builder.add_node("publish", publish_to_social)

        # =================================================================
        # EDGE DEFINITIONS
        # =================================================================

        # Evidence Layer Flow
        builder.add_edge(START, "aggregate")
        builder.add_edge("aggregate", "deduplicate")
        builder.add_edge("deduplicate", "categorize")

        # Bridge Detection (runs after categorization)
        builder.add_edge("categorize", "detect_bridges")
        builder.add_edge("detect_bridges", "select_bridge")

        # Parallel Fact Extraction (fan-out from bridge selection)
        builder.add_edge("select_bridge", "extract_local_facts")
        builder.add_edge("select_bridge", "extract_business_facts")
        builder.add_edge("select_bridge", "extract_ai_facts")

        # Parallel Persona Projection (after each fact extraction)
        builder.add_edge("extract_local_facts", "project_local")
        builder.add_edge("extract_business_facts", "project_business")
        builder.add_edge("extract_ai_facts", "project_ai")

        # Fan-in to compile script (wait for all persona projections)
        builder.add_edge("project_local", "compile_script")
        builder.add_edge("project_business", "compile_script")
        builder.add_edge("project_ai", "compile_script")

        # Script Review Gate
        builder.add_edge("compile_script", "script_review")

        # Conditional routing after script review
        builder.add_conditional_edges(
            "script_review",
            self._route_after_script_review,
            {
                "generate_video": "generate_video",
                "revise_script": "revise_script",
                "end": END,
            }
        )

        # Revision loop back to compilation
        builder.add_edge("revise_script", "compile_script")

        # Video Review Gate
        builder.add_edge("generate_video", "video_review")

        # Conditional routing after video review
        builder.add_conditional_edges(
            "video_review",
            self._route_after_video_review,
            {
                "publish": "publish",
                "end": END,
            }
        )

        builder.add_edge("publish", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _route_after_script_review(self, state: MayaState) -> str:
        """Route after script review based on DRR decision."""
        # Check the latest DRR for script review
        drrs = state.get("design_rationale_records", [])
        script_drrs = [d for d in drrs if d.get("review_type") == "script"]

        if not script_drrs:
            # No review yet, stay at review gate
            return "end"

        latest_drr = script_drrs[-1]

        if latest_drr.get("approved"):
            return "generate_video"

        # Check revision count
        revision_count = state.get("revision_count", 0)
        max_revisions = state.get("max_revisions", 3)

        if revision_count >= max_revisions:
            return "end"  # Max revisions reached, fail gracefully

        return "revise_script"

    def _route_after_video_review(self, state: MayaState) -> str:
        """Route after video review based on DRR decision."""
        drrs = state.get("design_rationale_records", [])
        video_drrs = [d for d in drrs if d.get("review_type") == "video"]

        if not video_drrs:
            return "end"

        latest_drr = video_drrs[-1]

        if latest_drr.get("approved"):
            return "publish"

        return "end"  # Video rejection ends the pipeline

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    async def start_briefing(
        self,
        week_number: Optional[int] = None,
        year: Optional[int] = None,
        language_code: str = "en-SG",
    ) -> Dict[str, Any]:
        """Start a new weekly briefing pipeline."""
        today = date.today()
        week_number = week_number or today.isocalendar()[1]
        year = year or today.year

        initial_state = create_initial_state(week_number, year, language_code)
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
            "language_code": language_code,
        }

    async def submit_script_review(
        self,
        thread_id: str,
        approved: bool,
        rejection_categories: Optional[List[str]] = None,
        feedback_text: Optional[str] = None,
        problematic_segment_ids: Optional[List[str]] = None,
        suggested_revisions: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit structured script review (Pattern E.9: DRR).

        Args:
            thread_id: The pipeline thread ID
            approved: Whether the script is approved
            rejection_categories: List of RejectionCategory values if rejected
            feedback_text: Detailed feedback text
            problematic_segment_ids: IDs of segments with issues
            suggested_revisions: Specific revision suggestions
            reviewer_id: ID of the reviewer (for audit trail)

        Returns:
            Updated pipeline status
        """
        config = {"configurable": {"thread_id": thread_id}}

        # Create the Design Rationale Record
        drr = DesignRationaleRecord(
            review_type="script",
            thread_id=thread_id,
            approved=approved,
            rejection_categories=[
                RejectionCategory(cat) for cat in (rejection_categories or [])
            ],
            feedback_text=feedback_text,
            problematic_segment_ids=problematic_segment_ids or [],
            suggested_revisions=suggested_revisions,
            reviewer_id=reviewer_id,
        )

        # Get current state to capture original content
        current_state = await self.get_state(thread_id)
        if current_state and current_state.get("draft_script"):
            drr.original_content = current_state["draft_script"].get("full_script", "")

        # Build state update
        update: Dict[str, Any] = {
            "design_rationale_records": [drr.model_dump()],
            "pending_review_type": None,
        }

        if approved:
            # Move draft to approved
            update["approved_script"] = current_state.get("draft_script") if current_state else None
            if update["approved_script"]:
                update["approved_script"]["status"] = "approved"
                update["approved_script"]["approved_at"] = datetime.utcnow().isoformat()
            update["status"] = PipelineStatus.GENERATING_VIDEO
        else:
            # Increment revision count
            update["revision_count"] = (current_state.get("revision_count", 0) + 1) if current_state else 1
            update["status"] = PipelineStatus.SYNTHESIZING  # Back to synthesis

        # Log DRR to database for fine-tuning
        await self._log_drr_to_database(drr)

        # Resume the pipeline
        result = await self.graph.ainvoke(update, config=config)

        # Update database
        await self._sync_to_database(thread_id, result, approved, "script")

        return {
            "thread_id": thread_id,
            "status": result.get("status", PipelineStatus.AWAITING_SCRIPT_APPROVAL).value,
            "approved": approved,
            "revision_count": result.get("revision_count", 0),
            "drr_id": drr.id,
        }

    async def submit_video_review(
        self,
        thread_id: str,
        approved: bool,
        rejection_categories: Optional[List[str]] = None,
        feedback_text: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit structured video review (Pattern E.9: DRR)."""
        config = {"configurable": {"thread_id": thread_id}}

        drr = DesignRationaleRecord(
            review_type="video",
            thread_id=thread_id,
            approved=approved,
            rejection_categories=[
                RejectionCategory(cat) for cat in (rejection_categories or [])
            ],
            feedback_text=feedback_text,
            reviewer_id=reviewer_id,
        )

        update: Dict[str, Any] = {
            "design_rationale_records": [drr.model_dump()],
            "pending_review_type": None,
            "status": PipelineStatus.PUBLISHING if approved else PipelineStatus.FAILED,
        }

        # Log DRR
        await self._log_drr_to_database(drr)

        # Resume pipeline
        result = await self.graph.ainvoke(update, config=config)

        # Update database
        await self._sync_to_database(thread_id, result, approved, "video")

        return {
            "thread_id": thread_id,
            "status": result.get("status", PipelineStatus.COMPLETED).value,
            "approved": approved,
            "drr_id": drr.id,
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

    async def get_provenance_chain(
        self,
        thread_id: str,
        fact_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get full provenance chain for a fact (Pattern A.10).

        Returns the chain: Fact -> NewsItem -> Source URL
        """
        state = await self.get_state(thread_id)
        if not state:
            return None

        from .state import trace_fact_to_source
        return trace_fact_to_source(state, fact_id)

    async def get_review_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all Design Rationale Records for a thread (Pattern E.9)."""
        state = await self.get_state(thread_id)
        if not state:
            return []

        return state.get("design_rationale_records", [])

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    async def _log_drr_to_database(self, drr: DesignRationaleRecord) -> None:
        """Log Design Rationale Record to database for fine-tuning data."""
        db = get_db_service()

        # Store in a dedicated table for fine-tuning
        # This creates training data: (original_content, rejection_reason, revised_content)
        try:
            # Mock implementation - would use actual Supabase table
            if db.mock_mode:
                print(f"[DRR Logged] {drr.review_type}: approved={drr.approved}, "
                      f"categories={drr.rejection_categories}")
            else:
                # In production, insert into design_rationale_records table
                pass
        except Exception as e:
            print(f"Failed to log DRR: {e}")

    async def _sync_to_database(
        self,
        thread_id: str,
        result: Dict[str, Any],
        approved: bool,
        review_type: str,
    ) -> None:
        """Sync pipeline state to database."""
        db = get_db_service()
        briefing = await db.get_briefing_by_thread(thread_id)

        if not briefing:
            return

        from app.models.schemas import WeeklyBriefingUpdate

        update_data = {
            "status": PipelineStatus(result.get("status", PipelineStatus.AGGREGATING)),
        }

        if review_type == "script" and approved:
            approved_script = result.get("approved_script", {})
            update_data.update({
                "full_script": approved_script.get("full_script"),
                "script_approved_at": datetime.utcnow(),
            })
        elif review_type == "video" and approved:
            update_data.update({
                "video_approved_at": datetime.utcnow(),
                "published_at": datetime.utcnow() if result.get("status") == PipelineStatus.COMPLETED else None,
            })

        await db.update_briefing(briefing.id, WeeklyBriefingUpdate(**update_data))


# =============================================================================
# SINGLETON
# =============================================================================

_pipeline: Optional[MayaPipeline] = None


def get_pipeline() -> MayaPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MayaPipeline()
    return _pipeline
