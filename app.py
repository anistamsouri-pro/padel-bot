"""
app.py — Backend FastAPI pour le Padel Bot
Lance avec : python app.py
Accède sur : http://127.0.0.1:8000
"""

import os
import json
import subprocess
from datetime import datetime, date, timedelta, time as time_module
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / "index.html"
AGENT_DIR = Path.home() / "padel-agent"

app = FastAPI(title="Padel Bot")

# Serve static files (hero.jpg, etc.) from the padel-agent directory
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    """Sert la page principale."""
    return FileResponse(str(INDEX_PATH), media_type="text/html")


class BookingConfig(BaseModel):
    target_date: str          # ISO 'YYYY-MM-DD'
    target_time: str          # 'HH:MM'
    court_priority: list[str] # ['D4', 'D5', ...]
    dry_run: bool = False
    headless: bool = False


@app.post("/api/schedule")
async def schedule(cfg: BookingConfig):
    """Reçoit la config depuis le formulaire et lance le bot en arrière-plan."""

    # Validation
    if not cfg.court_priority:
        return JSONResponse({"ok": False, "error": "Au moins un terrain requis"}, status_code=400)

    # Parse date / time
    target_date = date.fromisoformat(cfg.target_date)
    hour, minute = map(int, cfg.target_time.split(":"))

    # Compute opening time
    weekday = target_date.weekday()  # 0 = lundi, 6 = dimanche
    if weekday < 5:
        opening_dt = datetime.combine(target_date - timedelta(days=2), time_module(17, 0))
    else:
        opening_dt = datetime.combine(target_date - timedelta(days=1), time_module(19, 30))

    date_offset = (target_date - date.today()).days

    config = {
        "target_date_offset": date_offset,
        "target_hour": hour,
        "target_minute": minute,
        "court_priority": cfg.court_priority,
        "opening_iso": opening_dt.isoformat(),
        "dry_run": cfg.dry_run,
        "headless": cfg.headless,
    }

    # Save config
    AGENT_DIR.mkdir(exist_ok=True)
    config_path = AGENT_DIR / "booking_config.json"
    log_path = AGENT_DIR / "bot.log"

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # Launch bot in background
    cmd = (
        f"cd {AGENT_DIR} && "
        f"source .venv/bin/activate && "
        f"python reserve_with_config.py > {log_path} 2>&1 &"
    )
    try:
        subprocess.Popen(["/bin/bash", "-c", cmd])
        return {
            "ok": True,
            "opening_iso": opening_dt.isoformat(),
            "log_path": str(log_path),
            "config_path": str(config_path),
            "message": "Bot lancé en arrière-plan.",
        }
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/api/status")
async def status():
    """Renvoie les dernières lignes du log + l'état du process."""
    log_path = AGENT_DIR / "bot.log"
    if not log_path.exists():
        return {"running": False, "log": ""}

    with open(log_path) as f:
        lines = f.readlines()
    last = "".join(lines[-40:]) if lines else ""

    # Heuristique : le process tourne si le dernier log n'est pas "FIN DU SCRIPT"
    running = "FIN DU SCRIPT" not in last and "ÉCHEC" not in last
    return {"running": running, "log": last}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n  🎾  Padel Bot — http://127.0.0.1:8000\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, log_level="warning")
