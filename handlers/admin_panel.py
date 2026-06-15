# handlers/admin_panel.py
"""Админки: старосты (над своей группой) и глобальная (владелец/модераторы)."""
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
)
from handlers.start import get_main_keyboard
from database.db_operations import (
    get_user_by_telegram_id, get_group_by_id,
    can_manage_group, create_invite, list_group_invites,
    list_group_members, set_member_role, remove_member,
    list_institutions, create_institution, set_global_role,
)


# ── Утилиты ────────────────────────────────────────────────────────────────────

async def _bot_username(message: types.Message) -> str:
    me = await message.bot.get_me()
    return me.username


def _invite_link(bot_username: str, code: str) -> str:
    return f"https://t.me/{bot_username}?start={code}"


def _role_label(role: str) -> str:
    return {"owner": "👑 Староста", "helper": "🛠 Помощник", "member": "👤 Участник"}.get(role, role)


# ── Вход в админку старосты ────────────────────────────────────────────────────

async def open_group_admin(message: types.Message):
    user = get_user_by_telegram_id(telegram_id=message.from_user.id)
    if not user or not user.active_group_id:
        await message.answer("⚠️ Сначала войди в группу. Напиши /start")
        return
    if not can_manage_group(message.from_user.id, user.active_group_id):
        await message.answer("🔒 Управление группой доступно только старосте.")
        return
    group = get_group_by_id(user.active_group_id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔗 Ссылка-приглашение в группу", callback_data="ga_invite"))
    kb.add(InlineKeyboardButton("👥 Участники и помощники", callback_data="ga_members"))
    await message.answer(
        f"⚙️ Управление группой «{group.name}»\n\n"
        "Здесь ты можешь пригласить одногруппников и назначить помощников.",
        reply_markup=kb,
    )


# ── Коллбэки админки старосты ──────────────────────────────────────────────────

async def group_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    user = get_user_by_telegram_id(telegram_id=user_id)
    if not user or not user.active_group_id or not can_manage_group(user_id, user.active_group_id):
        await callback_query.answer("Нет доступа", show_alert=True)
        return
    group_id = user.active_group_id

    if data == "ga_invite":
        # Берём существующую активную join-ссылку или создаём новую.
        existing = [i for i in list_group_invites(group_id)
                    if i.invite_type == "join_group" and i.is_active]
        invite = existing[0] if existing else create_invite(
            "join_group", group_id=group_id, created_by=user_id)
        if not invite:
            await callback_query.message.answer("❌ Не удалось создать ссылку.")
            await callback_query.answer()
            return
        bot_un = await _bot_username(callback_query.message)
        link = _invite_link(bot_un, invite.code)
        await callback_query.message.answer(
            "🔗 Ссылка-приглашение в группу (можно кидать в общий чат):\n\n"
            f"{link}\n\n"
            "По ней одногруппники войдут как обычные участники.\n"
            f"Код: {invite.code}"
        )
        await callback_query.answer()
        return

    if data == "ga_members":
        await _show_members(callback_query, group_id)
        return

    if data.startswith("ga_promote_"):
        target = int(data.replace("ga_promote_", ""))
        set_member_role(group_id, target, "helper")
        await callback_query.answer("Назначен помощником ✅")
        await _show_members(callback_query, group_id, edit=True)
        return

    if data.startswith("ga_demote_"):
        target = int(data.replace("ga_demote_", ""))
        set_member_role(group_id, target, "member")
        await callback_query.answer("Снят до участника ✅")
        await _show_members(callback_query, group_id, edit=True)
        return

    if data.startswith("ga_kick_"):
        target = int(data.replace("ga_kick_", ""))
        if target == group_id:  # защита от абсурда, не сработает, оставлено для ясности
            pass
        remove_member(group_id, target)
        await callback_query.answer("Удалён из группы ✅")
        await _show_members(callback_query, group_id, edit=True)
        return


async def _show_members(callback_query, group_id, edit=False):
    members = list_group_members(group_id)
    owner_id = callback_query.from_user.id
    kb = InlineKeyboardMarkup(row_width=1)
    lines = ["👥 Участники группы:\n"]
    for m in members:
        u = get_user_by_telegram_id(telegram_id=m.user_id)
        name = u.first_name if u else str(m.user_id)
        lines.append(f"{_role_label(m.group_role)} — {name}")
        if m.group_role == "owner":
            continue  # старосту не трогаем
        if m.group_role == "member":
            kb.add(InlineKeyboardButton(
                f"⬆️ Сделать помощником: {name}", callback_data=f"ga_promote_{m.user_id}"))
        elif m.group_role == "helper":
            kb.add(InlineKeyboardButton(
                f"⬇️ Снять помощника: {name}", callback_data=f"ga_demote_{m.user_id}"))
        kb.add(InlineKeyboardButton(
            f"❌ Удалить: {name}", callback_data=f"ga_kick_{m.user_id}"))
    text = "\n".join(lines) if len(lines) > 1 else "В группе пока только ты."
    if edit:
        try:
            await callback_query.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback_query.message.answer(text, reply_markup=kb)
    else:
        await callback_query.message.answer(text, reply_markup=kb)
    await callback_query.answer()


# ── Глобальная админка ─────────────────────────────────────────────────────────

async def open_global_admin(message: types.Message):
    user = get_user_by_telegram_id(telegram_id=message.from_user.id)
    if not user or user.global_role != "admin":
        await message.answer("🔒 Раздел только для администратора.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎓 Выдать ссылку на создание группы", callback_data="gl_create_link"))
    kb.add(InlineKeyboardButton("🏛 Список заведений", callback_data="gl_institutions"))
    await message.answer(
        "🛠 Админ-панель\n\n"
        "Выдавай старостам ссылки на создание групп и управляй заведениями.",
        reply_markup=kb,
    )


async def global_admin_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    user = get_user_by_telegram_id(telegram_id=user_id)
    if not user or user.global_role != "admin":
        await callback_query.answer("Нет доступа", show_alert=True)
        return

    if data == "gl_create_link":
        insts = list_institutions()
        kb = InlineKeyboardMarkup(row_width=1)
        for inst in insts:
            kb.add(InlineKeyboardButton(
                f"🏛 {inst.name}", callback_data=f"gl_linkfor_{inst.id}"))
        kb.add(InlineKeyboardButton("➕ Без привязки к заведению", callback_data="gl_linkfor_0"))
        await callback_query.message.answer(
            "К какому заведению привязать создаваемую группу?\n"
            "(староста сможет создать группу в этом заведении)",
            reply_markup=kb,
        )
        await callback_query.answer()
        return

    if data.startswith("gl_linkfor_"):
        inst_id = int(data.replace("gl_linkfor_", ""))
        institution_id = inst_id if inst_id != 0 else None
        invite = create_invite("create_group", institution_id=institution_id, created_by=user_id)
        if not invite:
            await callback_query.message.answer("❌ Не удалось создать ссылку.")
            await callback_query.answer()
            return
        bot_un = await _bot_username(callback_query.message)
        link = _invite_link(bot_un, invite.code)
        await callback_query.message.answer(
            "🎓 Одноразовая ссылка для старосты на создание группы:\n\n"
            f"{link}\n\n"
            "Отдай её старосте — он перейдёт, введёт название и станет владельцем группы.\n"
            f"Код: {invite.code}"
        )
        await callback_query.answer()
        return

    if data == "gl_institutions":
        insts = list_institutions()
        if not insts:
            await callback_query.message.answer("Заведений пока нет. Добавь через SQL или позже через бота.")
        else:
            txt = "🏛 Заведения:\n\n" + "\n".join(
                f"• {i.name}" + (f" ({i.city})" if i.city else "") +
                (f" — расписание: {i.schedule_provider}" if i.schedule_provider else "")
                for i in insts
            )
            await callback_query.message.answer(txt)
        await callback_query.answer()
        return
