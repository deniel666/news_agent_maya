"""Maya AI News Anchor - Main FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import date

from app.core.config import settings
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    print(f"Starting Maya AI News Anchor v1.0.0")
    print(f"Environment: {'Debug' if settings.debug else 'Production'}")

    yield

    # Shutdown
    print("Shutting down Maya AI News Anchor")

    # Cleanup resources
    from app.services.news_aggregator import get_news_aggregator
    aggregator = get_news_aggregator()
    await aggregator.close()


app = FastAPI(
    title="Maya AI News Anchor",
    description="Automated AI-powered news anchor for Southeast Asia",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Maya AI News Anchor",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }


@app.post("/trigger-weekly-briefing")
async def trigger_weekly_briefing():
    """Manual trigger for weekly briefing (cron endpoint)."""
    from fastapi import BackgroundTasks
    from app.agents.pipeline import get_pipeline

    today = date.today()
    week_number = today.isocalendar()[1]
    year = today.year

    pipeline = get_pipeline()

    # Run in background
    import asyncio
    asyncio.create_task(pipeline.start_briefing(week_number, year))

    return {
        "status": "started",
        "thread_id": f"{year}-W{week_number:02d}",
        "week_number": week_number,
        "year": year,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
