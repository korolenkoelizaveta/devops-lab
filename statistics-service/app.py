import asyncio
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import mean

import httpx
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(title="Gym Statistics Service", version="1.0.0")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000").rstrip("/")

@app.get("/health")
def health():
    return {"status": "ok"}

def _auth_headers(request: Request) -> dict[str, str]:
    return {
        k: request.headers[k]
        for k in ("cookie", "authorization")
        if k in request.headers
    }

async def get_django_data(request: Request, *paths: str) -> tuple:
    headers = _auth_headers(request)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            responses = await asyncio.gather(*(
                client.get(f"{BACKEND_URL}{path}", headers=headers)
                for path in paths
            ))
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Django API unavailable") from exc

    results = []
    for response in responses:
        if response.status_code in (401, 403):
            raise HTTPException(status_code=response.status_code, detail="Access denied by Django")
        if not response.is_success:
            raise HTTPException(status_code=502, detail="Django API returned an error")
        try:
            results.append(response.json())
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid JSON returned by Django") from exc
    return tuple(results)

def _rows(data: object, label: str) -> list[dict]:
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise HTTPException(status_code=502, detail=f"Unexpected {label} format")
    return data

def _profile_role(profile: dict) -> tuple[bool, str | None]:
    authenticated = bool(profile.get("is_authenticated"))
    admin_or_guest = (not authenticated) or bool(profile.get("is_admin")) or bool(profile.get("is_superuser"))
    return admin_or_guest, profile.get("role")

def _empty_user_stats() -> dict:
    return {
        "count": 0, "clients": 0, "trainers": 0,
        "min_id": None, "max_id": None, "avg_id": None,
    }

@app.get("/api/users/stats/")
async def users_stats(request: Request):
    profile, users = await get_django_data(request, "/api/userprofile/info/", "/api/users/")
    users = _rows(users, "users")
    admin_or_guest, role = _profile_role(profile)

    if admin_or_guest:
        users = [u for u in users if u.get("role") != "admin"]
        ids = [int(u["id"]) for u in users]
        return {
            "count": len(users),
            "clients": sum(u.get("role") == "client" for u in users),
            "trainers": sum(u.get("role") == "trainer" for u in users),
            "min_id": min(ids) if ids else None,
            "max_id": max(ids) if ids else None,
            "avg_id": float(mean(ids)) if ids else None,
        }

    if role == "client":
        trainers = sum(u.get("role") == "trainer" for u in users)
        return {**_empty_user_stats(), "count": trainers, "trainers": trainers}

    if role == "trainer":
        clients = sum(u.get("role") == "client" for u in users)
        return {**_empty_user_stats(), "count": clients, "clients": clients}

    return _empty_user_stats()


@app.get("/api/membershiptype/stats/")
async def membership_type_stats(request: Request):
    types, memberships = await get_django_data(
        request, "/api/membershiptype/", "/api/membership/"
    )
    types = _rows(types, "membership types")
    memberships = _rows(memberships, "memberships")

    clients_by_type: dict[int, set[int]] = defaultdict(set)
    for m in memberships:
        if m.get("membership_type") is not None and m.get("client") is not None:
            clients_by_type[int(m["membership_type"])].add(int(m["client"]))

    return [
        {
            "id": t["id"],
            "type": t["type"],
            "users_count": len(clients_by_type[int(t["id"])])
        }
        for t in types
    ]

@app.get("/api/membership/stats/")
async def membership_stats(request: Request):
    (memberships,) = await get_django_data(request, "/api/membership/")
    memberships = _rows(memberships, "memberships")
    active = sum(m.get("is_active") is True for m in memberships)
    return {
        "count": len(memberships),
        "active": active,
        "inactive": sum(m.get("is_active") is False for m in memberships),
    }

def _as_utc(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="Invalid workout date") from exc
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)

def _top(sessions: list[dict], key: str, names: dict[int, str]):
    counts = Counter(int(s[key]) for s in sessions if s.get(key) is not None)
    if not counts:
        return None, None
    top_id, count = counts.most_common(1)[0]
    return names.get(top_id), count

def _empty_workout_stats() -> dict:
    return {
        "total": 0, "last_7_days": 0, "upcoming": 0,
        "avg_per_client": 0.0,
        "top_trainer_name": None, "top_trainer_sessions": None,
        "top_client_name": None, "top_client_sessions": None,
    }

@app.get("/api/workoutsession/stats/")
async def workout_stats(request: Request):
    profile, sessions, users = await get_django_data(
        request, "/api/userprofile/info/", "/api/workoutsession/", "/api/users/"
    )
    sessions = _rows(sessions, "workout sessions")
    users = _rows(users, "users")
    admin_or_guest, role = _profile_role(profile)

    if not admin_or_guest and role not in ("client", "trainer"):
        return _empty_workout_stats()

    names = {int(u["id"]): u["name"] for u in users}
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    dates = [_as_utc(s["session_date"]) for s in sessions]
    total = len(sessions)
    last_7_days = sum(week_ago <= d <= now for d in dates)
    upcoming = sum(d > now for d in dates)
    clients = {s["client"] for s in sessions if s.get("client") is not None}
    avg_per_client = (
        float(total / len(clients))
        if clients and (admin_or_guest or role == "trainer") else 0.0
    )

    trainer_name, trainer_count = (None, None)
    client_name, client_count = (None, None)
    if admin_or_guest or role == "client":
        trainer_name, trainer_count = _top(sessions, "trainer", names)
    if admin_or_guest or role == "trainer":
        client_name, client_count = _top(sessions, "client", names)

    return {
        "total": total,
        "last_7_days": last_7_days,
        "upcoming": upcoming,
        "avg_per_client": avg_per_client,
        "top_trainer_name": trainer_name,
        "top_trainer_sessions": trainer_count,
        "top_client_name": client_name,
        "top_client_sessions": client_count,
    }
