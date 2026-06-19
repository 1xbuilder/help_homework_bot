# admin_auth.py
"""Аутентификация веб-админки: логин/пароль из переменных окружения + подписанные
токены сессии. Без сторонних зависимостей (только стандартная библиотека).

Переменные окружения (задаются в панели bothost):
  ADMIN_PANEL_LOGIN          — логин (например 'admin')
  ADMIN_PANEL_PASSWORD_HASH  — хэш пароля в формате pbkdf2_sha256$iters$salt$hash
                               (сгенерировать утилитой make_password.py)
  ADMIN_PANEL_SECRET         — длинная случайная строка для подписи токенов
                               (например secrets.token_hex(32))

Токен сессии — это data.signature, где:
  data      = base64url(JSON {"login":..., "exp": unix_ts})
  signature = base64url(HMAC-SHA256(secret, data))
Подделать токен без знания SECRET нельзя. Срок жизни — TOKEN_TTL.
"""
import os
import json
import time
import hmac
import base64
import hashlib

TOKEN_TTL = 60 * 60 * 12  # 12 часов


# Переменные окружения читаем ЖИВЫМИ при каждом обращении, а не один раз при
# импорте — чтобы значение не «застывало», если окружение поднялось позже.
def _env(name):
    return os.getenv(name, "")


# Совместимость: код и диагностика обращаются к admin_auth.ADMIN_LOGIN и т.п.
# Это обычные строки, но мы обновляем их перед каждой проверкой через _refresh().
ADMIN_LOGIN = _env("ADMIN_PANEL_LOGIN")
ADMIN_PASSWORD_HASH = _env("ADMIN_PANEL_PASSWORD_HASH")
ADMIN_SECRET = _env("ADMIN_PANEL_SECRET")


def _refresh():
    """Перечитывает env в модульные атрибуты (на случай позднего поднятия окружения)."""
    global ADMIN_LOGIN, ADMIN_PASSWORD_HASH, ADMIN_SECRET
    ADMIN_LOGIN = _env("ADMIN_PANEL_LOGIN")
    ADMIN_PASSWORD_HASH = _env("ADMIN_PANEL_PASSWORD_HASH")
    ADMIN_SECRET = _env("ADMIN_PANEL_SECRET")


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


# ── Пароли ─────────────────────────────────────────────────────────────────────

def hash_password(password: str, iterations: int = 200_000) -> str:
    """Создаёт строку pbkdf2_sha256$iters$salt$hash. Использовать в make_password.py."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Проверяет пароль против хранимого хэша. Защита от тайминг-атак — compare_digest."""
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


# ── Токены сессии ──────────────────────────────────────────────────────────────

def issue_token(login: str) -> str:
    secret = _env("ADMIN_PANEL_SECRET")
    payload = {"login": login, "exp": int(time.time()) + TOKEN_TTL}
    data = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest())
    return f"{data}.{sig}"


def verify_token(token: str) -> bool:
    """True, если токен валиден по подписи и не истёк."""
    secret = _env("ADMIN_PANEL_SECRET")
    if not token or not secret:
        return False
    try:
        data, sig = token.split(".", 1)
        expected = _b64e(
            hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return False
        payload = json.loads(_b64d(data))
        if int(payload.get("exp", 0)) < int(time.time()):
            return False
        return True
    except Exception:
        return False


# ── Проверка логина ────────────────────────────────────────────────────────────

def check_credentials(login: str, password: str) -> bool:
    _refresh()
    env_login = _env("ADMIN_PANEL_LOGIN")
    env_hash = _env("ADMIN_PANEL_PASSWORD_HASH")
    env_secret = _env("ADMIN_PANEL_SECRET")
    if not (env_login and env_hash and env_secret):
        # Конфигурация не задана — вход запрещён (чтобы не пускать с пустыми env).
        return False
    if not hmac.compare_digest(login or "", env_login):
        return False
    return verify_password(password or "", env_hash)


def is_configured() -> bool:
    return bool(_env("ADMIN_PANEL_LOGIN") and _env("ADMIN_PANEL_PASSWORD_HASH")
                and _env("ADMIN_PANEL_SECRET"))
