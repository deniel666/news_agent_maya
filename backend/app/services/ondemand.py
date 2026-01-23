"""Service for on-demand article-to-video generation."""

import httpx
from typing import List, Optional
from uuid import UUID
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.core.config import settings
from app.models.sources import Language
from app.services.database import get_db_service
from app.services.telegram_bot import get_telegram_bot
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client


# Prompts for different languages
SCRIPT_PROMPT_EN = """You are Maya, a professional AI news anchor for Southeast Asian audiences.

Your style is:
- Warm, relatable, conversational—like a trusted friend sharing news
- Culturally aware of Malaysian, Singaporean, and broader SEA context
- Uses occasional local expressions naturally (e.g., "lah", "kan")
- Explains news with relevance to SEA viewers

Rewrite this article as a news anchor script for Maya to present:

ARTICLE:
{article_content}

Guidelines:
1. Opening hook (1-2 sentences to grab attention)
2. Main content (rewritten in Maya's voice, 3-5 key points)
3. Closing with relevance to SEA audience
4. Target: 60-90 seconds (~150-225 words)

Write the script in English:
"""

SCRIPT_PROMPT_MS = """Anda adalah Maya, seorang pembaca berita AI profesional untuk penonton Asia Tenggara.

Gaya anda adalah:
- Mesra, mudah didekati, perbualan—seperti kawan yang dipercayai berkongsi berita
- Peka budaya Malaysia, Singapura, dan konteks Asia Tenggara
- Menggunakan ungkapan tempatan secara semulajadi (contoh: "lah", "kan")
- Menerangkan berita dengan kaitan kepada penonton Asia Tenggara

Tulis semula artikel ini sebagai skrip pembaca berita untuk Maya:

ARTIKEL:
{article_content}

Panduan:
1. Pembukaan yang menarik perhatian (1-2 ayat)
2. Kandungan utama (ditulis semula dalam suara Maya, 3-5 perkara utama)
3. Penutup dengan kaitan kepada penonton Asia Tenggara
4. Sasaran: 60-90 saat (~150-225 patah perkataan)

Tulis skrip dalam Bahasa Melayu:
"""

CAPTION_PROMPT_EN = """Create a social media caption for this news video.
Keep it engaging, include emojis, and end with relevant hashtags.
Max 200 characters for the main text, then hashtags.

Topic: {title}
Summary: {summary}

Caption (English):
"""

CAPTION_PROMPT_MS = """Cipta kapsyen media sosial untuk video berita ini.
Jadikan ia menarik, gunakan emoji, dan akhiri dengan hashtag yang relevan.
Maksimum 200 aksara untuk teks utama, kemudian hashtag.

Topik: {title}
Ringkasan: {summary}

Kapsyen (Bahasa Melayu):
"""


class OnDemandService:
    """Service for processing on-demand article-to-video requests."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,
        )

    async def process_article(
        self,
        job_id: UUID,
        article_url: str,
        languages: List[Language],
        platforms: List[str],
    ):
        """Process an article through the full pipeline."""
        db = get_db_service()

        try:
            # Step 1: Scrape article
            await db.update_ondemand_status(job_id, "scraping")
            content, title = await self._scrape_article(article_url)

            await db.update_ondemand_content(job_id, content, title)

            # Step 2: Generate scripts in requested languages
            await db.update_ondemand_status(job_id, "generating_script")
            scripts = {}
            captions = {}

            for lang in languages:
                script = await self._generate_script(content, lang)
                caption = await self._generate_caption(title, script[:200], lang)
                scripts[lang.value] = script
                captions[lang.value] = caption

            await db.update_ondemand_scripts(job_id, scripts, captions)

            # Step 3: Send for approval via Telegram
            await db.update_ondemand_status(job_id, "awaiting_approval")
            await self._send_telegram_approval(job_id, title, scripts)

        except Exception as e:
            await db.update_ondemand_status(job_id, "failed", error=str(e))
            raise

    async def _scrape_article(self, url: str) -> tuple[str, str]:
        """Scrape article content from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                follow_redirects=True,
                timeout=30.0,
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Try to extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        # Try to extract main content
        # Common article content selectors
        content_selectors = [
            "article",
            "[itemprop='articleBody']",
            ".article-content",
            ".post-content",
            ".entry-content",
            ".story-body",
            "main",
        ]

        content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove unwanted elements
                for unwanted in element.select("script, style, nav, header, footer, .ad, .advertisement"):
                    unwanted.decompose()

                paragraphs = element.find_all("p")
                content = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                if len(content) > 200:
                    break

        if not content:
            # Fallback to all paragraphs
            paragraphs = soup.find_all("p")
            content = "\n\n".join(p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True))

        # Limit content length
        if len(content) > 5000:
            content = content[:5000] + "..."

        return content, title

    async def _generate_script(self, content: str, language: Language) -> str:
        """Generate Maya script from article content."""
        if language == Language.ENGLISH:
            prompt = SCRIPT_PROMPT_EN.format(article_content=content)
        else:
            prompt = SCRIPT_PROMPT_MS.format(article_content=content)

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _generate_caption(self, title: str, summary: str, language: Language) -> str:
        """Generate social media caption."""
        if language == Language.ENGLISH:
            prompt = CAPTION_PROMPT_EN.format(title=title, summary=summary)
        else:
            prompt = CAPTION_PROMPT_MS.format(title=title, summary=summary)

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def _send_telegram_approval(
        self,
        job_id: UUID,
        title: str,
        scripts: dict,
    ):
        """Send approval request via Telegram."""
        bot = get_telegram_bot()
        await bot.send_script_approval(
            job_id=str(job_id),
            job_type="on_demand",
            title=title,
            scripts=scripts,
        )

    async def generate_videos(self, job_id: UUID):
        """Generate videos for approved scripts."""
        db = get_db_service()
        heygen = get_heygen_client()

        job = await db.get_ondemand_job(job_id)
        if not job:
            raise ValueError("Job not found")

        try:
            await db.update_ondemand_status(job_id, "generating_video")

            video_urls = {}

            # Generate video for each language
            if job.script_en:
                result = await heygen.generate_video(job.script_en)
                status = await heygen.wait_for_video(result["video_id"])
                video_urls["en"] = status["video_url"]

            if job.script_ms:
                # Note: You might need a different voice_id for Malay
                result = await heygen.generate_video(job.script_ms)
                status = await heygen.wait_for_video(result["video_id"])
                video_urls["ms"] = status["video_url"]

            await db.update_ondemand_videos(job_id, video_urls)

            # Send video approval request
            await db.update_ondemand_status(job_id, "awaiting_video_approval")

            bot = get_telegram_bot()
            await bot.send_video_approval(
                job_id=str(job_id),
                job_type="on_demand",
                video_urls=video_urls,
            )

        except Exception as e:
            await db.update_ondemand_status(job_id, "failed", error=str(e))
            raise

    async def publish_to_social(self, job_id: UUID):
        """Publish videos to social platforms."""
        db = get_db_service()
        blotato = get_blotato_client()

        job = await db.get_ondemand_job(job_id)
        if not job:
            raise ValueError("Job not found")

        try:
            await db.update_ondemand_status(job_id, "publishing")

            results = []

            # Publish English version
            if job.video_url_en and job.caption_en:
                result = await blotato.schedule_multi_platform(
                    video_url=job.video_url_en,
                    caption=job.caption_en,
                    platforms=job.platforms,
                    hashtags=["MayaNews", "SEANews", "BreakingNews"],
                )
                results.append({"language": "en", "posts": result["posts"]})

            # Publish Malay version
            if job.video_url_ms and job.caption_ms:
                result = await blotato.schedule_multi_platform(
                    video_url=job.video_url_ms,
                    caption=job.caption_ms,
                    platforms=job.platforms,
                    hashtags=["MayaNews", "BeritaMalaysia", "BeritaTerkini"],
                )
                results.append({"language": "ms", "posts": result["posts"]})

            await db.update_ondemand_status(job_id, "completed")
            await db.update_ondemand_published(job_id)

            # Notify via Telegram
            bot = get_telegram_bot()
            await bot.send_published_notification(
                job_id=str(job_id),
                platforms=job.platforms,
            )

        except Exception as e:
            await db.update_ondemand_status(job_id, "failed", error=str(e))
            raise

    async def regenerate_scripts(self, job_id: UUID):
        """Regenerate scripts for a job."""
        db = get_db_service()

        job = await db.get_ondemand_job(job_id)
        if not job:
            raise ValueError("Job not found")

        scripts = {}
        captions = {}

        for lang_str in job.languages:
            lang = Language(lang_str)
            script = await self._generate_script(job.original_content, lang)
            caption = await self._generate_caption(job.title, script[:200], lang)
            scripts[lang.value] = script
            captions[lang.value] = caption

        await db.update_ondemand_scripts(job_id, scripts, captions)
        await db.update_ondemand_status(job_id, "awaiting_approval")

        # Send for re-approval
        bot = get_telegram_bot()
        await bot.send_script_approval(
            job_id=str(job_id),
            job_type="on_demand",
            title=job.title,
            scripts=scripts,
        )


# Singleton
_ondemand_service: Optional[OnDemandService] = None


def get_ondemand_service() -> OnDemandService:
    global _ondemand_service
    if _ondemand_service is None:
        _ondemand_service = OnDemandService()
    return _ondemand_service
