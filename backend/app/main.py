import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.core.security_headers import BodySizeLimitMiddleware, SecurityHeadersMiddleware
from app.db.database import init_db
from app.routers import alerts, auth, camera, chat, crop, farms, fertilizer, irrigation, robot, sensors, sms, soil_health, weather, ws, yield_prediction
from app.services.hardware_poller import run_hardware_poller_loop
from app.services.simulator import run_simulator_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_stop_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _stop_event.clear()
    simulator_task = asyncio.create_task(run_simulator_loop(_stop_event))
    hardware_task = asyncio.create_task(run_hardware_poller_loop(_stop_event))
    yield
    _stop_event.set()
    await simulator_task
    await hardware_task


app = FastAPI(title="AgriNova API", version="1.0.0", lifespan=lifespan)

app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    # Also allow any device on the same private LAN (e.g. a phone hitting
    # the dev machine's 192.168.x.x:5173 address) without hardcoding an IP
    # that changes across networks/DHCP renewals.
    allow_origin_regex=r"http://(192\.168|10\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1]))\.\d{1,3}\.\d{1,3}:5173",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(sensors.router)
app.include_router(irrigation.router)
app.include_router(crop.router)
app.include_router(fertilizer.router)
app.include_router(soil_health.router)
app.include_router(yield_prediction.router)
app.include_router(robot.router)
app.include_router(camera.router)
app.include_router(alerts.router)
app.include_router(weather.router)
app.include_router(chat.router)
app.include_router(sms.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {"status": "online", "system": "AgriNova API"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
