import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.staticfiles import StaticFiles


from app.api import auth, roles, goals, password, user_info, training
from app.services.cleanup import delete_unverified_users
from app.services.cassandra import cassandra_service

logger = logging.getLogger("uvicorn")
scheduler = AsyncIOScheduler()
app.mount("/static", StaticFiles(directory="static"), name="static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск при старте приложения
    scheduler.add_job(
        delete_unverified_users,
        trigger="interval",
        hours=1,
        id="cleanup_unverified_users"
    )
    scheduler.start()
    logger.info("[Scheduler] Запущен")

    # Подключение к Cassandra
    try:
        cassandra_service.connect()
        logger.info("[Cassandra] Подключение установлено")
    except Exception as e:
        logger.error(f"[Cassandra] Ошибка подключения: {e}")

    yield

    # Остановка при выключении
    scheduler.shutdown()
    logger.info("[Scheduler] Остановлен")
    cassandra_service.close()
    logger.info("[Cassandra] Подключение закрыто")

app = FastAPI(
    lifespan=lifespan,
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
app.include_router(training.router)

@app.get("/")
async def root():
    return {"message": "Smart Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}