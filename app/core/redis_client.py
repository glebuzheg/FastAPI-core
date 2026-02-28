import logging
from contextlib import asynccontextmanager
from typing import Optional, Any, AsyncGenerator

from redis.asyncio import Redis, ConnectionPool

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class RedisManager:
    """Менеджер подключений к Redis"""

    def __init__(self):
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[Redis] = None
        self._initialized = False

    async def initialize(self):
        """Инициализация подключения к Redis"""
        if self._initialized:
            logger.warning("Redis уже инициализирован")
            return

        try:
            # Создание пула соединений
            self.pool = ConnectionPool.from_url(
                settings.REDIS_DSN,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            )

            # Создание клиента
            self.client = Redis.from_pool(self.pool)

            # Проверка подключения
            await self.client.ping()

            self._initialized = True
            logger.info("Redis успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации Redis: {e}")
            raise

    async def close(self):
        """Закрытие всех подключений"""
        if self.client:
            await self.client.aclose()
        if self.pool:
            await self.pool.aclose()
        self._initialized = False
        logger.info("Redis подключения закрыты")

    # Упрощенный метод без @asynccontextmanager
    def get_client(self) -> Redis:
        """Получение клиента Redis (не контекстный менеджер)"""
        if not self._initialized or not self.client:
            raise RuntimeError("Redis не инициализирован. Вызовите initialize()")
        return self.client

    @asynccontextmanager
    async def get_client_context(self) -> AsyncGenerator[Redis, None]:
        """
        Контекстный менеджер для получения клиента Redis
        Использование: async with redis_manager.get_client_context() as client:
        """
        if not self._initialized or not self.client:
            raise RuntimeError("Redis не инициализирован. Вызовите initialize()")

        try:
            yield self.client
        except Exception as e:
            logger.error(f"Ошибка Redis операции: {e}")
            raise

    async def health_check(self) -> bool:
        """Проверка здоровья подключения"""
        try:
            if self.client:
                return await self.client.ping()
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def set_value(self, key: str, value: Any, expire: Optional[int] = None):
        """Установка значения в Redis"""
        async with self.get_client_context() as client:
            await client.set(key, value, ex=expire)

    async def get_value(self, key: str) -> Optional[Any]:
        """Получение значения из Redis"""
        async with self.get_client_context() as client:
            return await client.get(key)

    async def delete_key(self, key: str):
        """Удаление ключа из Redis"""
        async with self.get_client_context() as client:
            await client.delete(key)


# Глобальный экземпляр менеджера
redis_manager = RedisManager()


# Функция для получения менеджера Redis
def get_redis_manager() -> RedisManager:
    """Получение экземпляра RedisManager"""
    return redis_manager


# Функция для внедрения зависимости
async def get_redis() -> Redis:
    """Dependency для получения клиента Redis"""
    if not redis_manager.client:
        raise RuntimeError("Redis клиент не инициализирован")
    return redis_manager.client


# Контекстный менеджер для использования в зависимостях
@asynccontextmanager
async def get_redis_context() -> AsyncGenerator[Redis, None]:
    """Контекстный менеджер для получения клиента Redis"""
    async with redis_manager.get_client_context() as client:
        yield client
