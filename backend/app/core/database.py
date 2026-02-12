"""Database connection module using Supabase."""

from supabase import create_client, Client
from .config import settings

try:
    # Create Supabase client instance
    # Use placeholders if not configured to avoid import errors during testing
    url = settings.supabase_url or "https://placeholder.supabase.co"
    key = settings.supabase_key or "placeholder"

    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"Warning: Supabase client initialization failed: {e}")
    supabase = None

__all__ = ["supabase"]
