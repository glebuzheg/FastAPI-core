import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_settings, db_manager, get_db, redis_manager, get_redis, Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    Запуск: инициализация подключений
    Завершение: закрытие подключений
    """
    # Startup
    logger.info("Starting up...")
    try:
        # Инициализация БД
        await db_manager.initialize()

        # Создание таблиц (только для разработки)
        if settings.ENVIRONMENT == "development":
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        # Инициализация Redis
        await redis_manager.initialize()

        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    try:
        await db_manager.close()
        await redis_manager.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Создание приложения FastAPI
app = FastAPI(
    title="FastAPI Core Module",
    description="Основной модуль с PostgreSQL и Redis",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Корневой маршрут"""
    return {
        "message": "FastAPI Core Module",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check(
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis)
):
    """Проверка здоровья сервиса и подключений"""
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "environment": settings.ENVIRONMENT
    }
    # Проверка DB
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = f"error: {str(e)}"

    # Проверка Redis
    try:
        await redis.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["redis"] = f"error: {str(e)}"

    return health_status
