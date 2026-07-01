from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import Signal, Snapshot
from app.scanner import Scanner

settings = get_settings()
templates = Jinja2Templates(directory="app/templates")
scanner = Scanner(settings)
scheduler = AsyncIOScheduler()


async def scheduled_scan() -> None:
    try:
        await scanner.scan_once()
    except Exception as exc:
        print(f"scan failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.add_job(scheduled_scan, "interval", seconds=settings.scan_interval_seconds, max_instances=1)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Binance Short Monitor", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with SessionLocal() as session:
        snapshots = (await session.execute(select(Snapshot).order_by(desc(Snapshot.created_at)).limit(50))).scalars().all()
        signals = (await session.execute(select(Signal).order_by(desc(Signal.created_at)).limit(20))).scalars().all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "snapshots": snapshots, "signals": signals})


@app.get("/api/snapshots")
async def api_snapshots(limit: int = 100):
    async with SessionLocal() as session:
        rows = (await session.execute(select(Snapshot).order_by(desc(Snapshot.created_at)).limit(limit))).scalars().all()
    return rows


@app.get("/api/signals")
async def api_signals(limit: int = 100):
    async with SessionLocal() as session:
        rows = (await session.execute(select(Signal).order_by(desc(Signal.created_at)).limit(limit))).scalars().all()
    return rows


@app.post("/api/scan/run")
async def run_scan():
    return await scanner.scan_once()
