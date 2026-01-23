"""Editorial Agent - LangGraph agent for story curation and ranking."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID, uuid4

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from ..core.config import settings


class EditorialState(TypedDict):
    """State for the editorial review workflow."""
    # Input
    raw_stories: List[Dict[str, Any]]
    guidelines: List[Dict[str, Any]]
    brand_profile: Optional[Dict[str, Any]]
    week_number: int
    year: int

    # Processing
    current_story_index: int
    scored_stories: List[Dict[str, Any]]

    # Output
    executive_summary: str
    key_themes: List[str]
    recommendations: List[Dict[str, Any]]
    editorial_notes: str

    # Metadata
    error: Optional[str]


class EditorialAgent:
    """Agent for reviewing and ranking news stories based on editorial guidelines."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY,
        )
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for editorial review."""
        workflow = StateGraph(EditorialState)

        # Add nodes
        workflow.add_node("prepare_context", self._prepare_context)
        workflow.add_node("score_stories", self._score_stories)
        workflow.add_node("identify_themes", self._identify_themes)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("create_recommendations", self._create_recommendations)

        # Define edges
        workflow.set_entry_point("prepare_context")
        workflow.add_edge("prepare_context", "score_stories")
        workflow.add_edge("score_stories", "identify_themes")
        workflow.add_edge("identify_themes", "generate_summary")
        workflow.add_edge("generate_summary", "create_recommendations")
        workflow.add_edge("create_recommendations", END)

        return workflow.compile()

    def _build_guidelines_prompt(self, guidelines: List[Dict], brand_profile: Optional[Dict]) -> str:
        """Build the guidelines context for the AI."""
        prompt_parts = []

        if brand_profile:
            prompt_parts.append(f"""
BRAND PROFILE:
- Name: {brand_profile.get('name', 'N/A')}
- Mission: {brand_profile.get('mission', 'N/A')}
- Vision: {brand_profile.get('vision', 'N/A')}
- Target Audience: {brand_profile.get('target_audience', 'N/A')}
- Tone of Voice: {brand_profile.get('tone_of_voice', 'N/A')}
- Content Pillars: {', '.join(brand_profile.get('content_pillars', []))}
- Values: {', '.join(brand_profile.get('values', []))}

{brand_profile.get('ai_prompt_context', '')}
""")

        # Group guidelines by category
        guidelines_by_category = {}
        for g in guidelines:
            if g.get('enabled', True):
                cat = g.get('category', 'other')
                if cat not in guidelines_by_category:
                    guidelines_by_category[cat] = []
                guidelines_by_category[cat].append(g)

        prompt_parts.append("\nEDITORIAL GUIDELINES:")
        for category, items in guidelines_by_category.items():
            prompt_parts.append(f"\n{category.upper().replace('_', ' ')}:")
            for item in items:
                weight_indicator = "★" * int(item.get('weight', 1))
                prompt_parts.append(f"  - {item['name']} [{weight_indicator}]: {item['criteria']}")

        return "\n".join(prompt_parts)

    async def _prepare_context(self, state: EditorialState) -> EditorialState:
        """Prepare the context for editorial review."""
        state["current_story_index"] = 0
        state["scored_stories"] = []
        state["error"] = None
        return state

    async def _score_stories(self, state: EditorialState) -> EditorialState:
        """Score and rank all stories based on guidelines."""
        guidelines_context = self._build_guidelines_prompt(
            state["guidelines"],
            state.get("brand_profile")
        )

        scored_stories = []

        # Process stories in batches for efficiency
        batch_size = 10
        stories = state["raw_stories"]

        for i in range(0, len(stories), batch_size):
            batch = stories[i:i + batch_size]

            stories_text = "\n\n---\n\n".join([
                f"STORY {j+1} (ID: {s['id']}):\nTitle: {s['title']}\nSource: {s['source_name']} ({s['source_type']})\nCategory: {s.get('category', 'N/A')}\n\nContent:\n{s['content_markdown'][:2000]}..."
                if len(s.get('content_markdown', '')) > 2000
                else f"STORY {j+1} (ID: {s['id']}):\nTitle: {s['title']}\nSource: {s['source_name']} ({s['source_type']})\nCategory: {s.get('category', 'N/A')}\n\nContent:\n{s.get('content_markdown', '')}"
                for j, s in enumerate(batch, start=i)
            ])

            prompt = f"""You are an editorial AI assistant helping curate news stories for a media company.

{guidelines_context}

SCORING CRITERIA:
- Score each story from 0-100 based on alignment with brand and guidelines
- Assign a rank: top_priority (80-100), high (60-79), medium (40-59), low (20-39), rejected (0-19)
- Provide a brief reason for the ranking

STORIES TO REVIEW:
{stories_text}

Respond with a JSON array of objects, one per story:
[
  {{
    "story_id": "uuid-here",
    "score": 85,
    "rank": "top_priority",
    "reason": "Highly relevant to AI technology pillar, timely, aligns with target audience interests",
    "suggested_angle": "Focus on the business implications for SMEs",
    "key_points": ["point 1", "point 2"]
  }}
]

Only output the JSON array, no other text."""

            try:
                response = await self.llm.ainvoke(prompt)
                content = response.content.strip()

                # Clean up response if needed
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]

                batch_scores = json.loads(content)
                scored_stories.extend(batch_scores)

            except Exception as e:
                # On error, assign default low scores
                for s in batch:
                    scored_stories.append({
                        "story_id": s["id"],
                        "score": 25,
                        "rank": "low",
                        "reason": f"Error during scoring: {str(e)}",
                        "suggested_angle": None,
                        "key_points": []
                    })

        state["scored_stories"] = scored_stories
        return state

    async def _identify_themes(self, state: EditorialState) -> EditorialState:
        """Identify key themes across the reviewed stories."""
        # Get top stories for theme analysis
        top_stories = [s for s in state["scored_stories"] if s.get("rank") in ["top_priority", "high"]]

        if not top_stories:
            state["key_themes"] = ["No significant themes identified this week"]
            return state

        # Get story details
        story_details = []
        for scored in top_stories[:20]:  # Limit to top 20
            for raw in state["raw_stories"]:
                if str(raw["id"]) == str(scored["story_id"]):
                    story_details.append({
                        "title": raw["title"],
                        "category": raw.get("category"),
                        "reason": scored.get("reason", "")
                    })
                    break

        prompt = f"""Analyze these top-ranked news stories and identify 3-5 key themes for the week.

Stories:
{json.dumps(story_details, indent=2)}

Respond with a JSON array of theme strings, e.g.:
["AI adoption in Southeast Asian SMEs", "Regional tech policy changes", "Voice technology innovation"]

Only output the JSON array."""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            state["key_themes"] = json.loads(content)
        except Exception:
            state["key_themes"] = ["Theme analysis unavailable"]

        return state

    async def _generate_summary(self, state: EditorialState) -> EditorialState:
        """Generate executive summary of the editorial review."""
        stats = {
            "total": len(state["scored_stories"]),
            "top_priority": len([s for s in state["scored_stories"] if s.get("rank") == "top_priority"]),
            "high": len([s for s in state["scored_stories"] if s.get("rank") == "high"]),
            "medium": len([s for s in state["scored_stories"] if s.get("rank") == "medium"]),
            "low": len([s for s in state["scored_stories"] if s.get("rank") == "low"]),
            "rejected": len([s for s in state["scored_stories"] if s.get("rank") == "rejected"]),
        }

        avg_score = sum(s.get("score", 0) for s in state["scored_stories"]) / max(len(state["scored_stories"]), 1)

        prompt = f"""Write a brief executive summary (2-3 paragraphs) for the editorial review of Week {state['week_number']}, {state['year']}.

STATISTICS:
- Total stories reviewed: {stats['total']}
- Top Priority: {stats['top_priority']}
- High: {stats['high']}
- Medium: {stats['medium']}
- Low: {stats['low']}
- Rejected: {stats['rejected']}
- Average Score: {avg_score:.1f}/100

KEY THEMES: {', '.join(state['key_themes'])}

Write a professional summary highlighting:
1. Overall news landscape this week
2. Top opportunities for content
3. Any notable gaps or areas to monitor

Output only the summary text, no JSON."""

        try:
            response = await self.llm.ainvoke(prompt)
            state["executive_summary"] = response.content.strip()
        except Exception as e:
            state["executive_summary"] = f"Summary generation failed: {str(e)}"

        return state

    async def _create_recommendations(self, state: EditorialState) -> EditorialState:
        """Create final recommendations list."""
        recommendations = []

        # Sort by score descending
        sorted_stories = sorted(
            state["scored_stories"],
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        for scored in sorted_stories:
            # Find the raw story
            raw_story = None
            for raw in state["raw_stories"]:
                if str(raw["id"]) == str(scored["story_id"]):
                    raw_story = raw
                    break

            if raw_story:
                recommendations.append({
                    "raw_story_id": str(scored["story_id"]),
                    "title": raw_story["title"],
                    "rank": scored.get("rank", "low"),
                    "score": scored.get("score", 0),
                    "reason": scored.get("reason", ""),
                    "suggested_angle": scored.get("suggested_angle"),
                    "key_points": scored.get("key_points", [])
                })

        state["recommendations"] = recommendations

        # Generate editorial notes
        top_count = len([r for r in recommendations if r["rank"] == "top_priority"])
        prompt = f"""Based on this week's editorial review with {top_count} top priority stories, write brief editorial notes (2-3 sentences) with actionable advice for the content team.

Key themes: {', '.join(state['key_themes'])}

Output only the notes text."""

        try:
            response = await self.llm.ainvoke(prompt)
            state["editorial_notes"] = response.content.strip()
        except Exception:
            state["editorial_notes"] = "Focus on top priority stories for maximum impact."

        return state

    async def run_review(
        self,
        raw_stories: List[Dict[str, Any]],
        guidelines: List[Dict[str, Any]],
        brand_profile: Optional[Dict[str, Any]] = None,
        week_number: Optional[int] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run the full editorial review process."""
        now = datetime.utcnow()
        if week_number is None:
            week_number = now.isocalendar()[1]
        if year is None:
            year = now.year

        initial_state: EditorialState = {
            "raw_stories": raw_stories,
            "guidelines": guidelines,
            "brand_profile": brand_profile,
            "week_number": week_number,
            "year": year,
            "current_story_index": 0,
            "scored_stories": [],
            "executive_summary": "",
            "key_themes": [],
            "recommendations": [],
            "editorial_notes": "",
            "error": None
        }

        try:
            result = await self.workflow.ainvoke(initial_state)
            return {
                "success": True,
                "week_number": week_number,
                "year": year,
                "total_reviewed": len(result["scored_stories"]),
                "executive_summary": result["executive_summary"],
                "key_themes": result["key_themes"],
                "recommendations": result["recommendations"],
                "editorial_notes": result["editorial_notes"],
                "stats": {
                    "top_priority": len([r for r in result["recommendations"] if r["rank"] == "top_priority"]),
                    "high": len([r for r in result["recommendations"] if r["rank"] == "high"]),
                    "medium": len([r for r in result["recommendations"] if r["rank"] == "medium"]),
                    "low": len([r for r in result["recommendations"] if r["rank"] == "low"]),
                    "rejected": len([r for r in result["recommendations"] if r["rank"] == "rejected"]),
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "week_number": week_number,
                "year": year
            }

    async def score_single_story(
        self,
        story: Dict[str, Any],
        guidelines: List[Dict[str, Any]],
        brand_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Score a single story (for real-time ranking as stories come in)."""
        guidelines_context = self._build_guidelines_prompt(guidelines, brand_profile)

        prompt = f"""You are an editorial AI assistant. Score this news story based on the guidelines.

{guidelines_context}

STORY:
Title: {story['title']}
Source: {story.get('source_name', 'Unknown')} ({story.get('source_type', 'unknown')})
Category: {story.get('category', 'N/A')}

Content:
{story.get('content_markdown', '')[:3000]}

Score from 0-100 and assign rank: top_priority (80-100), high (60-79), medium (40-59), low (20-39), rejected (0-19)

Respond with JSON:
{{
  "score": 75,
  "rank": "high",
  "reason": "Brief explanation",
  "suggested_angle": "Optional angle suggestion",
  "key_points": ["key point 1", "key point 2"]
}}

Only output the JSON."""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception as e:
            return {
                "score": 25,
                "rank": "low",
                "reason": f"Scoring error: {str(e)}",
                "suggested_angle": None,
                "key_points": []
            }


# Singleton instance
editorial_agent = EditorialAgent()
