# make_password.py
"""Утилита для генерации значений для переменных окружения админ-панели.

Запусти ЛОКАЛЬНО (не на хостинге):
    python make_password.py

Скрипт спросит пароль, выведет готовые строки для ADMIN_PANEL_PASSWORD_HASH
и ADMIN_PANEL_SECRET — скопируй их в переменные окружения на bothost.
Сам пароль нигде не сохраняется.
"""
import secrets
import getpass
from admin_auth import hash_password


def main():
    print("Генерация настроек для веб-админки StudyFlow\n")
    login = input("Логин админа (например admin): ").strip() or "admin"

    pw1 = getpass.getpass("Пароль: ")
    pw2 = getpass.getpass("Повтори пароль: ")
    if pw1 != pw2:
        print("\n❌ Пароли не совпадают, запусти заново.")
        return
    if len(pw1) < 6:
        print("\n⚠️  Пароль короче 6 символов — лучше сделать длиннее.")

    pw_hash = hash_password(pw1)
    secret = secrets.token_hex(32)

    print("\n" + "=" * 60)
    print("Скопируй это в переменные окружения на bothost:\n")
    print(f"ADMIN_PANEL_LOGIN={login}")
    print(f"ADMIN_PANEL_PASSWORD_HASH={pw_hash}")
    print(f"ADMIN_PANEL_SECRET={secret}")
    print("=" * 60)
    print("\nПароль нигде не сохранён. Если забудешь — запусти утилиту заново.")


if __name__ == "__main__":
    main()
