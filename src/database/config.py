import streamlit as st
import os
from supabase import create_client, Client, ClientOptions

def get_supabase_credentials():
    url = ""
    key = ""
    if hasattr(st, "secrets"):
        try:
            for u in ["SUPABASE_URL", "supabase_url", "URL", "url"]:
                if u in st.secrets:
                    url = str(st.secrets[u])
                    break
            for k in ["SUPABASE_KEY", "supabase_key", "KEY", "key"]:
                if k in st.secrets:
                    key = str(st.secrets[k])
                    break
            if (not url or not key) and "supabase" in st.secrets:
                sub = st.secrets["supabase"]
                if hasattr(sub, "get"):
                    url = url or sub.get("SUPABASE_URL") or sub.get("url") or sub.get("supabase_url") or ""
                    key = key or sub.get("SUPABASE_KEY") or sub.get("key") or sub.get("supabase_key") or ""
        except Exception:
            pass
    if not url:
        url = os.environ.get("SUPABASE_URL", "") or os.environ.get("supabase_url", "")
    if not key:
        key = os.environ.get("SUPABASE_KEY", "") or os.environ.get("supabase_key", "")

    url = str(url).strip().strip('"').strip("'").rstrip('/')
    key = str(key).strip().strip('"').strip("'")
    return url, key

def is_supabase_configured():
    url, key = get_supabase_credentials()
    return bool(url and key and "your-project" not in url and "placeholder" not in url and "your-anon-key" not in key)

url, key = get_supabase_credentials()
supabase = None

if is_supabase_configured():
    try:
        options = ClientOptions(
            postgrest_client_timeout=60,
            storage_client_timeout=60,
            function_client_timeout=60
        )
        supabase = create_client(url, key, options=options)
    except Exception as e:
        supabase = None