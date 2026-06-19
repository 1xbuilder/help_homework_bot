# admin_api.py
"""REST API веб-админки. Подключается к aiohttp-приложению из photo_proxy.py.

Все роуты под /api/admin/*. Кроме /login требуют заголовок:
    Authorization: Bearer <токен>
Токен выдаётся /login и проверяется admin_auth.verify_token.

Service-ключ Supabase живёт ТОЛЬКО на сервере (внутри db_operations) и в браузер
не попадает — фронт ходит исключительно через эти роуты.

Вся работа с БД делегируется в database.db_operations, чтобы не дублировать логику.
"""
import json
import functools
from aiohttp import web

import admin_auth
from database import db_operations as ops


# ── CORS ───────────────────────────────────────────────────────────────────────
# Разрешаем фронт с GitHub Pages и localhost (для локальной отладки).
# Origin берётся из заголовка запроса; если он в белом списке — отражаем его.
ALLOWED_ORIGIN_SUFFIXES = (
    ".github.io",
    "localhost",
    "127.0.0.1",
)


def _cors_headers(request):
    origin = request.headers.get("Origin", "")
    allow = ""
    if origin:
        host_ok = any(
            origin.endswith(suf) or f"//{suf}" in origin or suf in origin
            for suf in ALLOWED_ORIGIN_SUFFIXES
        )
        allow = origin if host_ok else ""
    return {
        "Access-Control-Allow-Origin": allow or "*",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Max-Age": "86400",
    }


def _json(request, data, status=200):
    return web.json_response(data, status=status, headers=_cors_headers(request))


def _err(request, message, status=400):
    return web.json_response({"error": message}, status=status,
                             headers=_cors_headers(request))


# ── Декоратор авторизации ──────────────────────────────────────────────────────

def require_auth(handler):
    @functools.wraps(handler)
    async def wrapper(request):
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        if not admin_auth.verify_token(token):
            return _err(request, "Не авторизован", status=401)
        return await handler(request)
    return wrapper


async def _body(request):
    try:
        return await request.json()
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════════════════════

async def login(request):
    if request.method == "OPTIONS":
        return web.Response(headers=_cors_headers(request))
    if not admin_auth.is_configured():
        return _err(request, "Админка не настроена: задай ADMIN_PANEL_* в окружении", 503)
    data = await _body(request)
    login_v = (data.get("login") or "").strip()
    password = data.get("password") or ""
    if not admin_auth.check_credentials(login_v, password):
        return _err(request, "Неверный логин или пароль", 401)
    token = admin_auth.issue_token(login_v)
    return _json(request, {"token": token, "login": login_v})


@require_auth
async def me(request):
    return _json(request, {"ok": True})


# ═══════════════════════════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════════════════════════

def _user_dict(u):
    return {
        "id": u.id,
        "user_id": u.user_id,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "active_group_id": u.active_group_id,
        "global_role": u.global_role,
        "subgroup": u.subgroup,
    }


@require_auth
async def users_list(request):
    """GET /api/admin/users?q=поиск — список/поиск пользователей."""
    q = request.query.get("q", "").strip()
    if q:
        found = ops.search_users(q)
    else:
        # Полный список через прямой запрос (search_users требует строку).
        try:
            r = ops.supabase.table("users").select("*").order("created_at", desc=True).limit(500).execute()
            found = [ops.UserDTO(x) for x in r.data]
        except Exception as e:
            return _err(request, f"Ошибка БД: {e}", 500)
    return _json(request, {"users": [_user_dict(u) for u in found]})


@require_auth
async def user_get(request):
    uid = int(request.match_info["uid"])
    u = ops.get_user_by_telegram_id(telegram_id=uid)
    if not u:
        return _err(request, "Пользователь не найден", 404)
    # Подтянем его группы и роли.
    groups = []
    for m, g in ops.list_user_groups_detailed(uid):
        groups.append({"group_id": g.id, "group_name": g.name,
                       "group_role": m.group_role, "subgroup": m.subgroup,
                       "is_active": g.id == u.active_group_id})
    d = _user_dict(u)
    d["groups"] = groups
    return _json(request, d)


@require_auth
async def user_update(request):
    """PATCH /api/admin/users/{uid} — правка ника, имени, глобальной роли, активной группы."""
    uid = int(request.match_info["uid"])
    data = await _body(request)
    u = ops.get_user_by_telegram_id(telegram_id=uid)
    if not u:
        return _err(request, "Пользователь не найден", 404)

    # Имя
    if "first_name" in data and data["first_name"]:
        ops.update_user_name(uid, data["first_name"].strip())
    # Username (ник в системе) — отдельным апдейтом, такого хелпера нет — сделаем напрямую.
    updates = {}
    if "username" in data:
        updates["username"] = (data["username"] or "").strip() or None
    if "last_name" in data:
        updates["last_name"] = (data["last_name"] or "").strip() or None
    if "subgroup" in data:
        updates["subgroup"] = (data["subgroup"] or "").strip() or None
    if updates:
        try:
            ops.supabase.table("users").update(updates).eq("user_id", uid).execute()
        except Exception as e:
            return _err(request, f"Ошибка обновления: {e}", 500)
    # Глобальная роль
    if "global_role" in data and data["global_role"] in ("user", "moderator", "admin"):
        ops.set_global_role(uid, data["global_role"])
    # Активная группа
    if "active_group_id" in data:
        ops.set_active_group(uid, data["active_group_id"] or None)

    u = ops.get_user_by_telegram_id(telegram_id=uid)
    return _json(request, _user_dict(u))


@require_auth
async def user_delete(request):
    """DELETE /api/admin/users/{uid} — удалить пользователя целиком."""
    uid = int(request.match_info["uid"])
    try:
        ops.supabase.table("users").delete().eq("user_id", uid).execute()
        return _json(request, {"ok": True})
    except Exception as e:
        return _err(request, f"Ошибка удаления: {e}", 500)


# ═══════════════════════════════════════════════════════════════════════════════
#  INSTITUTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _inst_dict(i):
    return {"id": i.id, "name": i.name, "city": i.city,
            "schedule_provider": i.schedule_provider,
            "schedule_provider_id": i.schedule_provider_id}


@require_auth
async def institutions_list(request):
    insts = ops.list_institutions()
    out = []
    for i in insts:
        groups = ops.list_groups_by_institution(i.id)
        d = _inst_dict(i)
        d["groups_count"] = len(groups)
        out.append(d)
    return _json(request, {"institutions": out})


@require_auth
async def institution_create(request):
    data = await _body(request)
    name = (data.get("name") or "").strip()
    if len(name) < 2:
        return _err(request, "Название слишком короткое")
    inst = ops.create_institution(
        name=name,
        city=(data.get("city") or "").strip() or None,
        schedule_provider=(data.get("schedule_provider") or "").strip() or None,
    )
    if not inst:
        return _err(request, "Не удалось создать заведение", 500)
    return _json(request, _inst_dict(inst))


@require_auth
async def institution_update(request):
    iid = int(request.match_info["iid"])
    data = await _body(request)
    fields = {}
    for k in ("name", "city", "schedule_provider", "schedule_provider_id"):
        if k in data:
            fields[k] = (data[k] or "").strip() or None
    inst = ops.update_institution(iid, **fields)
    if not inst:
        return _err(request, "Не удалось обновить", 500)
    return _json(request, _inst_dict(inst))


@require_auth
async def institution_delete(request):
    iid = int(request.match_info["iid"])
    ops.delete_institution(iid)
    return _json(request, {"ok": True})


# ═══════════════════════════════════════════════════════════════════════════════
#  GROUPS
# ═══════════════════════════════════════════════════════════════════════════════

def _group_dict(g):
    return {"id": g.id, "institution_id": g.institution_id, "name": g.name,
            "external_schedule_id": g.external_schedule_id,
            "owner_user_id": g.owner_user_id}


@require_auth
async def groups_list(request):
    """GET /api/admin/groups?institution_id=N (опционально)."""
    iid = request.query.get("institution_id")
    if iid:
        groups = ops.list_groups_by_institution(int(iid))
    else:
        groups = ops.list_all_groups()
    out = []
    for g in groups:
        d = _group_dict(g)
        d["members_count"] = ops.count_group_members(g.id)
        out.append(d)
    return _json(request, {"groups": out})


@require_auth
async def group_get(request):
    gid = int(request.match_info["gid"])
    g = ops.get_group_by_id(gid)
    if not g:
        return _err(request, "Группа не найдена", 404)
    members = []
    for m in ops.list_group_members(gid):
        u = ops.get_user_by_telegram_id(telegram_id=m.user_id)
        members.append({
            "user_id": m.user_id,
            "group_role": m.group_role,
            "subgroup": m.subgroup,
            "first_name": u.first_name if u else None,
            "username": u.username if u else None,
        })
    d = _group_dict(g)
    d["members"] = members
    return _json(request, d)


@require_auth
async def group_create(request):
    data = await _body(request)
    name = (data.get("name") or "").strip()
    iid = data.get("institution_id")
    if len(name) < 2:
        return _err(request, "Название слишком короткое")
    if not iid:
        return _err(request, "Не указано заведение")
    g = ops.create_group(institution_id=int(iid), name=name,
                         owner_user_id=data.get("owner_user_id"),
                         external_schedule_id=(data.get("external_schedule_id") or None))
    if not g:
        return _err(request, f"Не удалось создать группу: {ops.LAST_ERROR}", 500)
    return _json(request, _group_dict(g))


@require_auth
async def group_update(request):
    gid = int(request.match_info["gid"])
    data = await _body(request)
    fields = {}
    if "name" in data and data["name"]:
        fields["name"] = data["name"].strip()
    if "external_schedule_id" in data:
        fields["external_schedule_id"] = (data["external_schedule_id"] or "").strip() or None
    if "institution_id" in data and data["institution_id"]:
        fields["institution_id"] = int(data["institution_id"])
    g = ops.update_group(gid, **fields)
    if not g:
        return _err(request, "Не удалось обновить группу", 500)
    return _json(request, _group_dict(g))


@require_auth
async def group_delete(request):
    gid = int(request.match_info["gid"])
    ops.delete_group(gid)
    return _json(request, {"ok": True})


@require_auth
async def group_member_set_role(request):
    """PATCH /api/admin/groups/{gid}/members/{uid} — сменить роль участника."""
    gid = int(request.match_info["gid"])
    uid = int(request.match_info["uid"])
    data = await _body(request)
    role = data.get("group_role")
    if role not in ("owner", "helper", "member"):
        return _err(request, "Недопустимая роль")
    ops.set_member_role(gid, uid, role)
    return _json(request, {"ok": True})


@require_auth
async def group_member_remove(request):
    gid = int(request.match_info["gid"])
    uid = int(request.match_info["uid"])
    ops.remove_member(gid, uid)
    return _json(request, {"ok": True})


@require_auth
async def group_member_add(request):
    """POST /api/admin/groups/{gid}/members — добавить участника по telegram user_id."""
    gid = int(request.match_info["gid"])
    data = await _body(request)
    uid = data.get("user_id")
    if not uid:
        return _err(request, "Не указан user_id")
    role = data.get("group_role", "member")
    if role not in ("owner", "helper", "member"):
        role = "member"
    m = ops.add_member(gid, int(uid), group_role=role,
                       subgroup=data.get("subgroup"))
    if not m:
        return _err(request, "Не удалось добавить участника", 500)
    return _json(request, {"ok": True})


# ═══════════════════════════════════════════════════════════════════════════════
#  HOMEWORKS
# ═══════════════════════════════════════════════════════════════════════════════

def _hw_dict(h):
    return {
        "id": h.id, "group_id": h.group_id, "subject": h.subject,
        "task": h.task, "date_for": str(h.date_for) if h.date_for else None,
        "subgroup": h.subgroup, "created_by": h.created_by,
        "attachment_file_id": h.attachment_file_id,
    }


@require_auth
async def homeworks_list(request):
    """GET /api/admin/homeworks?group_id=N — ДЗ группы (или всех, если не задано)."""
    gid = request.query.get("group_id")
    hws = ops.get_all_homeworks(group_id=int(gid) if gid else None)
    return _json(request, {"homeworks": [_hw_dict(h) for h in hws]})


@require_auth
async def homework_update(request):
    hid = int(request.match_info["hid"])
    data = await _body(request)
    h = ops.update_homework(
        homework_id=hid,
        subject=data.get("subject"),
        task=data.get("task"),
        date_for=data.get("date_for"),
        subgroup=data.get("subgroup"),
    )
    if not h:
        return _err(request, "Не удалось обновить ДЗ", 500)
    return _json(request, _hw_dict(h))


@require_auth
async def homework_delete(request):
    hid = int(request.match_info["hid"])
    ops.delete_homework(homework_id=hid)
    return _json(request, {"ok": True})


# ═══════════════════════════════════════════════════════════════════════════════
#  INVITES
# ═══════════════════════════════════════════════════════════════════════════════

def _invite_dict(i):
    return {"id": i.id, "code": i.code, "invite_type": i.invite_type,
            "group_id": i.group_id, "institution_id": i.institution_id,
            "is_active": i.is_active, "is_single_use": i.is_single_use,
            "uses_count": i.uses_count, "max_uses": i.max_uses}


@require_auth
async def invite_create(request):
    """POST /api/admin/invites {invite_type, institution_id?, group_id?}."""
    data = await _body(request)
    itype = data.get("invite_type")
    if itype not in ("create_group", "join_group"):
        return _err(request, "Недопустимый тип ссылки")
    inv = ops.create_invite(
        itype,
        group_id=data.get("group_id"),
        institution_id=data.get("institution_id"),
    )
    if not inv:
        return _err(request, "Не удалось создать ссылку", 500)
    return _json(request, _invite_dict(inv))


@require_auth
async def invite_deactivate(request):
    code = request.match_info["code"]
    ops.deactivate_invite(code)
    return _json(request, {"ok": True})


@require_auth
async def group_invites_list(request):
    gid = int(request.match_info["gid"])
    invites = ops.list_group_invites(gid)
    return _json(request, {"invites": [_invite_dict(i) for i in invites]})


# ═══════════════════════════════════════════════════════════════════════════════
#  Регистрация роутов
# ═══════════════════════════════════════════════════════════════════════════════

async def _options(request):
    return web.Response(headers=_cors_headers(request))


def register_admin_routes(app: web.Application):
    """Вызывается из photo_proxy.create_proxy_app(), добавляет роуты к приложению."""
    r = app.router

    # OPTIONS-preflight для всех админских путей
    r.add_route("OPTIONS", "/api/admin/{tail:.*}", _options)

    r.add_post("/api/admin/login", login)
    r.add_get("/api/admin/me", me)

    r.add_get("/api/admin/users", users_list)
    r.add_get("/api/admin/users/{uid}", user_get)
    r.add_patch("/api/admin/users/{uid}", user_update)
    r.add_delete("/api/admin/users/{uid}", user_delete)

    r.add_get("/api/admin/institutions", institutions_list)
    r.add_post("/api/admin/institutions", institution_create)
    r.add_patch("/api/admin/institutions/{iid}", institution_update)
    r.add_delete("/api/admin/institutions/{iid}", institution_delete)

    r.add_get("/api/admin/groups", groups_list)
    r.add_post("/api/admin/groups", group_create)
    r.add_get("/api/admin/groups/{gid}", group_get)
    r.add_patch("/api/admin/groups/{gid}", group_update)
    r.add_delete("/api/admin/groups/{gid}", group_delete)
    r.add_post("/api/admin/groups/{gid}/members", group_member_add)
    r.add_patch("/api/admin/groups/{gid}/members/{uid}", group_member_set_role)
    r.add_delete("/api/admin/groups/{gid}/members/{uid}", group_member_remove)
    r.add_get("/api/admin/groups/{gid}/invites", group_invites_list)

    r.add_get("/api/admin/homeworks", homeworks_list)
    r.add_patch("/api/admin/homeworks/{hid}", homework_update)
    r.add_delete("/api/admin/homeworks/{hid}", homework_delete)

    r.add_post("/api/admin/invites", invite_create)
    r.add_delete("/api/admin/invites/{code}", invite_deactivate)
