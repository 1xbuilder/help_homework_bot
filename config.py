import os
from dotenv import load_dotenv

# Загружаем .env из корня проекта (если есть). На хостинге переменные обычно
# заданы в окружении напрямую — тогда .env не нужен, load_dotenv просто ничего не сделает.
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or os.getenv("API_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_raw_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _raw_ids.split(",") if x.strip().isdigit()]
