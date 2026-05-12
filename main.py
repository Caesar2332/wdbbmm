from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv
import pathlib
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

app = FastAPI(title="Wedding Invitation — Бейбарыс & Малика")


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )


pathlib.Path("static").mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


def get_supabase() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
        options=ClientOptions(
            postgrest_client_timeout=60,
            storage_client_timeout=60,
            schema="public",
        ),
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "supabase_url": SUPABASE_URL,
        "supabase_key_len": len(SUPABASE_KEY),
        "env": os.getenv("RAILWAY_ENVIRONMENT", os.getenv("RENDER", "local")),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/rsvp")
async def update_rsvp(request: Request):
    try:
        body = await request.json()
        name = body.get("name", "").strip()
        if not name:
            return JSONResponse(status_code=400, content={"success": False, "error": "name_required"})
        get_supabase().table("guests").insert(
            {
                "full_name": name,
                "attendance_status": body.get("status", "Думаю"),
                "food_preference": body.get("food", ""),
                "guests_count": int(body.get("guests_count", 1)),
            }
        ).execute()
        return {"success": True}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
