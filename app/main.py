from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api import auth, roles, goals, password, user_info
from app.services.cleanup import delete_unverified_users

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск при старте приложения
    scheduler.add_job(
        delete_unverified_users,
        trigger="interval",
        hours=1,  # запускать каждый час
        id="cleanup_unverified_users"
    )
    scheduler.start()
    print("[Scheduler] Запущен")
    yield
    # Остановка при выключении
    scheduler.shutdown()
    print("[Scheduler] Остановлен")

app = FastAPI(
    title="Smart Tracker API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(roles.router)
app.include_router(goals.router)
app.include_router(password.router)
app.include_router(user_info.router)

@app.get("/")
async def root():
    return {"message": "Smart Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}