from fastapi import FastAPI, Request, Response, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv
from typing import Optional
import pathlib
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
WEDDING_CODE = os.getenv("WEDDING_CODE", "")

app = FastAPI(title="Wedding Invitation — Малика & Бейбарыс")

# Ensure static dir exists
pathlib.Path("static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def get_supabase(access_token: str = None, refresh_token: str = None) -> Client:
    client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
        options=ClientOptions(
            postgrest_client_timeout=60,
            storage_client_timeout=60,
            schema="public",
        ),
    )
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass
    return client


# ── Health check ───────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    sb_ok = bool(SUPABASE_URL and SUPABASE_KEY)
    return {
        "status": "ok",
        "supabase_url_set": sb_ok,
        "wedding_code_set": bool(WEDDING_CODE),
        "env": os.getenv("RAILWAY_ENVIRONMENT", os.getenv("RENDER", "local")),
    }


# ── Pages ──────────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Auth API ───────────────────────────────────────────────────────────────


@app.post("/api/login")
async def login(request: Request, response: Response):
    try:
        body = await request.json()
        sb = get_supabase()
        res = sb.auth.sign_in_with_password(
            {"email": body["email"], "password": body["password"]}
        )
        if res.user:
            _set_cookies(response, res.session.access_token, res.session.refresh_token)
            meta = res.user.user_metadata or {}
            return {"success": True, "full_name": meta.get("full_name", "Guest")}
        return JSONResponse(401, {"success": False, "error": "auth_failed"})
    except Exception as e:
        return JSONResponse(400, {"success": False, "error": str(e)})


@app.post("/api/register")
async def register(request: Request):
    try:
        body = await request.json()
        if body.get("wedding_code") != WEDDING_CODE:
            return JSONResponse(403, {"success": False, "error": "invalid_code"})
        sb = get_supabase()
        res = sb.auth.sign_up(
            {
                "email": body["email"],
                "password": body["password"],
                "options": {"data": {"full_name": body["name"]}},
            }
        )
        if res.user:
            return {"success": True}
        return JSONResponse(400, {"success": False, "error": "user_exists"})
    except Exception as e:
        err = str(e).lower()
        if "already" in err:
            return JSONResponse(409, {"success": False, "error": "user_exists"})
        return JSONResponse(400, {"success": False, "error": str(e)})


@app.post("/api/otp/send")
async def send_otp(request: Request):
    try:
        body = await request.json()
        sb = get_supabase()
        sb.auth.sign_in_with_otp({"email": body["email"]})
        return {"success": True}
    except Exception as e:
        return JSONResponse(400, {"success": False, "error": str(e)})


@app.post("/api/otp/verify")
async def verify_otp(request: Request, response: Response):
    try:
        body = await request.json()
        sb = get_supabase()
        res = sb.auth.verify_otp(
            {"email": body["email"], "token": body["token"], "type": "email"}
        )
        if res.user:
            _set_cookies(response, res.session.access_token, res.session.refresh_token)
            meta = res.user.user_metadata or {}
            return {"success": True, "full_name": meta.get("full_name", "Guest")}
        return JSONResponse(401, {"success": False, "error": "invalid_otp"})
    except Exception as e:
        return JSONResponse(400, {"success": False, "error": str(e)})


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"success": True}


# ── Guest API ──────────────────────────────────────────────────────────────


@app.get("/api/me")
async def get_me(
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
):
    if not access_token:
        return JSONResponse(401, {"success": False})
    try:
        sb = get_supabase(access_token, refresh_token)
        u_resp = sb.auth.get_user(access_token)
        if not (u_resp and u_resp.user):
            return JSONResponse(401, {"success": False})
        u = u_resp.user
        rows = sb.table("guests").select("*").eq("id", u.id).execute().data
        guest = rows[0] if rows else {}
        meta = u.user_metadata or {}
        return {
            "success": True,
            "full_name": meta.get("full_name", guest.get("full_name", "Guest")),
            "attendance_status": guest.get("attendance_status", "Думаю"),
            "food_preference": guest.get("food_preference", ""),
        }
    except Exception as e:
        return JSONResponse(401, {"success": False, "error": str(e)})


@app.post("/api/rsvp")
async def update_rsvp(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
):
    if not access_token:
        return JSONResponse(401, {"success": False})
    try:
        body = await request.json()
        sb = get_supabase(access_token, refresh_token)
        u_resp = sb.auth.get_user(access_token)
        if not (u_resp and u_resp.user):
            return JSONResponse(401, {"success": False})
        sb.table("guests").update(
            {"attendance_status": body["status"], "food_preference": body["food"]}
        ).eq("id", u_resp.user.id).execute()
        return {"success": True}
    except Exception as e:
        return JSONResponse(400, {"success": False, "error": str(e)})


@app.post("/api/change-password")
async def change_password(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
):
    if not access_token:
        return JSONResponse(401, {"success": False})
    try:
        body = await request.json()
        sb = get_supabase(access_token, refresh_token)
        sb.auth.update_user({"password": body["password"]})
        return {"success": True}
    except Exception as e:
        return JSONResponse(400, {"success": False, "error": str(e)})


# ── Helpers ────────────────────────────────────────────────────────────────


def _set_cookies(response: Response, access_token: str, refresh_token: str):
    # secure=True required for HTTPS (Railway/Render); works fine locally too
    is_prod = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER")
    response.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="none" if is_prod else "lax",
        secure=bool(is_prod), max_age=86400 * 7
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="none" if is_prod else "lax",
        secure=bool(is_prod), max_age=86400 * 30,
    )


# ── Run ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
