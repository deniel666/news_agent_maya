#!/usr/bin/env python3
"""
Maya AI News Anchor - Weekly Cron Trigger

This script is designed to be run by a cron job or scheduler.
It triggers the weekly briefing pipeline.

Usage:
  python cron_trigger.py                    # Run for current week
  python cron_trigger.py --week 5 --year 2026  # Run for specific week

Cron setup (Sunday 6 AM UTC / 2 PM SGT):
  0 6 * * 0 cd /app && python cron_trigger.py >> /var/log/maya.log 2>&1
"""

import asyncio
import argparse
import sys
from datetime import date
import httpx


async def trigger_via_api(backend_url: str, week_number: int, year: int) -> dict:
    """Trigger briefing via the API endpoint."""
    url = f"{backend_url}/trigger-weekly-briefing"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, timeout=30.0)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")


async def trigger_directly(week_number: int, year: int) -> dict:
    """Trigger briefing directly (when running in same environment)."""
    # Import here to avoid loading the full app when using API mode
    from app.agents.pipeline import get_pipeline

    pipeline = get_pipeline()
    result = await pipeline.start_briefing(week_number, year)
    return result


async def main():
    parser = argparse.ArgumentParser(description="Maya Weekly Briefing Trigger")
    parser.add_argument("--week", type=int, help="Week number (default: current week)")
    parser.add_argument("--year", type=int, help="Year (default: current year)")
    parser.add_argument("--api", type=str, help="Use API endpoint (provide URL)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")

    args = parser.parse_args()

    today = date.today()
    week_number = args.week or today.isocalendar()[1]
    year = args.year or today.year
    thread_id = f"{year}-W{week_number:02d}"

    print(f"=" * 50)
    print(f"Maya AI News Anchor - Weekly Briefing Trigger")
    print(f"=" * 50)
    print(f"Week: {week_number}")
    print(f"Year: {year}")
    print(f"Thread ID: {thread_id}")
    print(f"Mode: {'API' if args.api else 'Direct'}")
    print(f"=" * 50)

    if args.dry_run:
        print("DRY RUN - No action taken")
        return

    try:
        if args.api:
            print(f"Triggering via API: {args.api}")
            result = await trigger_via_api(args.api, week_number, year)
        else:
            print("Triggering directly...")
            result = await trigger_directly(week_number, year)

        print(f"\nPipeline started successfully!")
        print(f"Result: {result}")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
