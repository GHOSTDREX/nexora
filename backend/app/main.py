import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS
from app.db.database import init_db
from app.routers import alerts, auth, camera, chat, crop, farms, fertilizer, irrigation, robot, sensors, soil_health, weather, ws, yield_prediction
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(ws.router)


@app.get("/")
def root():
    return {"status": "online", "system": "AgriNova API"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
