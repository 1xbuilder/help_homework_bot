# database/db_session.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# override=False: не перебивать переменные окружения сервера значениями из .env
load_dotenv(override=False)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Не заданы SUPABASE_URL или SUPABASE_KEY в переменных окружения!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"✅ Подключено к Supabase через REST API: {SUPABASE_URL}")
