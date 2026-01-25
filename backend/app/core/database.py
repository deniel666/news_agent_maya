"""Database connection module using Supabase."""

from supabase import create_client, Client
from .config import settings

# Create Supabase client instance
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_key
)

__all__ = ["supabase"]
