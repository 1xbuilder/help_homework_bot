# database/db_session.py
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Не заданы SUPABASE_URL или SUPABASE_KEY в переменных окружения!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("✅ Подключено к Supabase через REST API")
