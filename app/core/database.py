import logging
from asyncio import current_task
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()


class DatabaseManager:
    """Менеджер подключений к PostgreSQL"""

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self.scoped_session: Optional[async_scoped_session] = None
        self._initialized = False

    async def initialize(self):
        """Инициализация подключения к базе данных"""
        if self._initialized:
            logger.warning("Database уже инициализирован")
            return

        try:
            # Создание движка
            self.engine = create_async_engine(
                settings.POSTGRES_DSN,
                echo=settings.POSTGRES_ECHO,
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
                pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
                pool_pre_ping=settings.POSTGRES_POOL_PRE_PING,
            )

            # Создание фабрики сессий
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Создание scoped session
            self.scoped_session = async_scoped_session(
                self.session_factory,
                scopefunc=current_task,
            )

            self._initialized = True
            logger.info("Database успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации database: {e}")
            raise

    async def close(self):
        """Закрытие всех подключений"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database подключения закрыты")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получение сессии базы данных (контекстный менеджер)"""
        if not self._initialized:
            raise RuntimeError("Database не инициализирован. Вызовите initialize()")

        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка сессии database: {e}")
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Проверка здоровья подключения"""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Глобальный экземпляр менеджера
db_manager = DatabaseManager()


# Функция для получения менеджера (добавлена для совместимости)
def get_db_manager() -> DatabaseManager:
    """Получение экземпляра DatabaseManager"""
    return db_manager


# Функция для внедрения зависимости
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения сессии базы данных"""
    async with db_manager.get_session() as session:
        yield session
