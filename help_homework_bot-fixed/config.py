import os

# Переменные берутся напрямую из окружения (панель хостинга)
# .env файл не нужен
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or os.getenv("API_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

_raw_ids = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _raw_ids.split(",") if x.strip().isdigit()]
