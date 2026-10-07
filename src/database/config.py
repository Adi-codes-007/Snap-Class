import streamlit as st
import os
from supabase import create_client, Client, ClientOptions

def get_supabase_credentials():
    url = ""
    key = ""
    if hasattr(st, "secrets"):
        try:
            url = st.secrets.get("SUPABASE_URL", "")
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            pass
    if not url:
        url = os.environ.get("SUPABASE_URL", "")
    if not key:
        key = os.environ.get("SUPABASE_KEY", "")
    return url, key

def is_supabase_configured():
    url, key = get_supabase_credentials()
    return bool(url and key and "your-project" not in url and "your-anon-key" not in key)

url, key = get_supabase_credentials()
try:
    options = ClientOptions(
        postgrest_client_timeout=60,
        storage_client_timeout=60,
        function_client_timeout=60
    )
    supabase: Client = create_client(
        url or "https://placeholder.supabase.co",
        key or "placeholder-key",
        options=options
    )
except Exception:
    supabase = None