"""Editorial Pipeline - Integrates news aggregation with editorial review system."""

import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..core.database import supabase
from ..models.schemas import NewsArticle
from .news_aggregator import get_news_aggregator
from .editorial_agent import editorial_agent


class EditorialPipelineService:
    """Service for integrating news aggregation with the editorial system."""

    def __init__(self):
        self.aggregator = get_news_aggregator()

    async def aggregate_and_store(
        self,
        days: int = 7,
        auto_score: bool = False,
        category_map: Optional[dict] = None
    ) -> dict:
        """
        Aggregate news from all sources and store as raw stories for editorial review.

        Args:
            days: Number of days to look back
            auto_score: Whether to automatically score stories after aggregation
            category_map: Optional mapping of source names to categories

        Returns:
            Summary of aggregated stories
        """
        # Default category mapping based on source
        if category_map is None:
            category_map = {
                "VentureBeat AI": "ai_tech",
                "TechInAsia": "ai_tech",
                "e27": "ai_tech",
                "CNA": "local",
                "Straits Times": "local",
                "Malay Mail": "local",
                "The Star": "local",
                "SCMP SEA": "business",
                "Nikkei Asia": "business",
            }

        # Aggregate from all sources
        articles = await self.aggregator.aggregate_all(days=days)

        # Store each article as a raw story
        stored_count = 0
        skipped_count = 0
        errors = []

        for article in articles:
            try:
                # Check for duplicates (by URL or title+source)
                if article.url:
                    existing = supabase.table("raw_stories").select("id").eq(
                        "original_url", article.url
                    ).execute()
                    if existing.data:
                        skipped_count += 1
                        continue

                # Convert to markdown format
                content_markdown = self._to_markdown(article)

                # Determine category
                category = category_map.get(article.source_name)
                if not category:
                    # Try to infer from content
                    category = self._infer_category(article.content or article.title or "")

                # Extract media URLs if any
                media_urls = self._extract_media_urls(article.content or "")

                # Create raw story
                raw_story_data = {
                    "title": article.title or self._generate_title(article.content),
                    "content_markdown": content_markdown,
                    "summary": self._generate_summary(article.content),
                    "source_name": article.source_name,
                    "source_type": article.source_type,
                    "original_url": article.url,
                    "media_urls": media_urls,
                    "category": category,
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                    "status": "pending",
                }

                response = supabase.table("raw_stories").insert(raw_story_data).execute()
                if response.data:
                    stored_count += 1

                    # Optionally auto-score
                    if auto_score and response.data[0]:
                        await self._score_story(response.data[0]["id"])

            except Exception as e:
                errors.append(f"{article.source_name}: {str(e)}")
                continue

        return {
            "total_fetched": len(articles),
            "stored": stored_count,
            "skipped_duplicates": skipped_count,
            "errors": errors
        }

    async def _score_story(self, story_id: str):
        """Score a single raw story."""
        try:
            # Get story
            story_response = supabase.table("raw_stories").select("*").eq(
                "id", story_id
            ).single().execute()
            if not story_response.data:
                return

            story = story_response.data

            # Get guidelines and brand profile
            guidelines_response = supabase.table("editorial_guidelines").select("*").eq(
                "enabled", True
            ).execute()
            guidelines = guidelines_response.data or []

            profile_response = supabase.table("brand_profile").select("*").limit(1).execute()
            brand_profile = profile_response.data[0] if profile_response.data else None

            # Score
            result = await editorial_agent.score_single_story(story, guidelines, brand_profile)

            # Update
            supabase.table("raw_stories").update({
                "status": "ranked",
                "score": result.get("score"),
                "rank": result.get("rank"),
                "rank_reason": result.get("reason"),
                "reviewed_at": datetime.utcnow().isoformat()
            }).eq("id", story_id).execute()

        except Exception as e:
            print(f"Error scoring story {story_id}: {e}")

    def _to_markdown(self, article: NewsArticle) -> str:
        """Convert a news article to markdown format."""
        parts = []

        if article.title:
            parts.append(f"# {article.title}\n")

        if article.source_name:
            parts.append(f"**Source:** {article.source_name}")

        if article.published_at:
            parts.append(f"**Published:** {article.published_at.strftime('%Y-%m-%d %H:%M')}")

        if article.url:
            parts.append(f"**Link:** [{article.url}]({article.url})")

        parts.append("")  # Empty line

        if article.content:
            parts.append(article.content)

        return "\n".join(parts)

    def _generate_title(self, content: str, max_length: int = 100) -> str:
        """Generate a title from content if none exists."""
        if not content:
            return "Untitled Story"

        # Take first sentence or first N characters
        first_sentence = content.split(".")[0].strip()
        if len(first_sentence) <= max_length:
            return first_sentence

        return content[:max_length].rsplit(" ", 1)[0] + "..."

    def _generate_summary(self, content: str, max_length: int = 300) -> Optional[str]:
        """Generate a brief summary from content."""
        if not content:
            return None

        # Take first paragraph or first N characters
        paragraphs = content.split("\n\n")
        first_para = paragraphs[0].strip() if paragraphs else content

        if len(first_para) <= max_length:
            return first_para

        return first_para[:max_length].rsplit(" ", 1)[0] + "..."

    def _infer_category(self, text: str) -> str:
        """Infer category from text content."""
        text_lower = text.lower()

        # AI/Tech keywords
        ai_keywords = ["ai", "artificial intelligence", "machine learning", "chatgpt",
                       "openai", "llm", "neural", "automation", "robot", "tech"]
        if any(kw in text_lower for kw in ai_keywords):
            return "ai_tech"

        # Business keywords
        business_keywords = ["business", "market", "stock", "investment", "economy",
                            "finance", "startup", "funding", "ipo", "revenue"]
        if any(kw in text_lower for kw in business_keywords):
            return "business"

        # Default to local
        return "local"

    def _extract_media_urls(self, content: str) -> List[str]:
        """Extract media URLs from content."""
        # Find image URLs
        img_pattern = r'https?://[^\s<>"]+?\.(?:jpg|jpeg|png|gif|webp)'
        images = re.findall(img_pattern, content, re.IGNORECASE)

        # Find video URLs
        video_pattern = r'https?://[^\s<>"]+?\.(?:mp4|webm|mov)'
        videos = re.findall(video_pattern, content, re.IGNORECASE)

        return list(set(images + videos))[:10]  # Limit to 10

    async def run_weekly_review(self, week_number: Optional[int] = None, year: Optional[int] = None):
        """
        Run the full editorial review for a week.
        This is typically called by a cron job.
        """
        now = datetime.utcnow()
        if week_number is None:
            week_number = now.isocalendar()[1]
        if year is None:
            year = now.year

        # Check if review already exists
        existing = supabase.table("editorial_reviews").select("id").eq(
            "year", year
        ).eq("week_number", week_number).execute()

        if existing.data:
            return {"error": f"Review already exists for week {week_number}, {year}"}

        # Get pending stories
        stories_response = supabase.table("raw_stories").select("*").eq(
            "status", "pending"
        ).execute()
        stories = stories_response.data or []

        if not stories:
            return {"error": "No pending stories to review"}

        # Get guidelines
        guidelines_response = supabase.table("editorial_guidelines").select("*").eq(
            "enabled", True
        ).execute()
        guidelines = guidelines_response.data or []

        # Get brand profile
        profile_response = supabase.table("brand_profile").select("*").limit(1).execute()
        brand_profile = profile_response.data[0] if profile_response.data else None

        # Run the editorial agent review
        result = await editorial_agent.run_review(
            raw_stories=stories,
            guidelines=guidelines,
            brand_profile=brand_profile,
            week_number=week_number,
            year=year
        )

        if result.get("success"):
            # Store review
            review_data = {
                "week_number": week_number,
                "year": year,
                "review_period_start": (now - datetime.timedelta(days=7)).isoformat(),
                "review_period_end": now.isoformat(),
                "status": "completed",
                "total_stories_reviewed": len(stories),
                "executive_summary": result.get("executive_summary"),
                "key_themes": result.get("key_themes", []),
                "recommendations": result.get("recommendations", []),
                "editorial_notes": result.get("editorial_notes"),
                "top_priority_count": result["stats"]["top_priority"],
                "high_count": result["stats"]["high"],
                "medium_count": result["stats"]["medium"],
                "low_count": result["stats"]["low"],
                "rejected_count": result["stats"]["rejected"],
                "completed_at": datetime.utcnow().isoformat()
            }
            supabase.table("editorial_reviews").insert(review_data).execute()

            # Update stories with scores
            for rec in result.get("recommendations", []):
                supabase.table("raw_stories").update({
                    "status": "ranked",
                    "score": rec.get("score"),
                    "rank": rec.get("rank"),
                    "rank_reason": rec.get("reason"),
                    "reviewed_at": datetime.utcnow().isoformat()
                }).eq("id", rec["raw_story_id"]).execute()

        return result

    async def get_top_stories(self, limit: int = 5) -> List[dict]:
        """Get top-ranked stories for content creation."""
        response = supabase.table("raw_stories").select("*").in_(
            "rank", ["top_priority", "high"]
        ).eq("status", "ranked").order(
            "score", desc=True
        ).limit(limit).execute()

        return response.data or []


# Singleton instance
_editorial_pipeline: Optional[EditorialPipelineService] = None


def get_editorial_pipeline() -> EditorialPipelineService:
    global _editorial_pipeline
    if _editorial_pipeline is None:
        _editorial_pipeline = EditorialPipelineService()
    return _editorial_pipeline
