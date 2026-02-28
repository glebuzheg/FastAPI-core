# Основной модуль FastAPI

Core модуль для FastAPI приложений с унифицированными интерфейсами для PostgreSQL и Redis.

---

## Разделение ответственности между компонентами

- **config.py**: Конфигурация приложения (Pydantic Settings v2)
- **database.py**: Управление подключениями к PostgreSQL (SQLAlchemy 2.0+)
- **redis_client.py**: Управление подключениями к Redis
- **main.py**: Точка входа, lifespan приложения, базовые маршруты
- **\_\_init\_\_.py**: Публичный API модуля

Каждый компонент имеет единственную ответственность, что упрощает поддержку и тестирование.

---

## Применение паттернов проектирования

| Паттерн | Где используется | Зачем |
|---------|------------------|-------|
| **Singleton** | `get_settings()` с `@lru_cache`, глобальные `db_manager` и `redis_manager` | Единственный экземпляр настроек и менеджеров |
| **Factory** | Создание движка SQLAlchemy, пула Redis, фабрики сессий | Централизованное создание сложных объектов |
| **Context Manager** | `get_session()`, `get_client_context()` с `@asynccontextmanager` | Автоматическое управление ресурсами |
| **Dependency Injection** | `get_db()`, `get_redis()` для FastAPI | Интеграция с DI системой, удобное тестирование |
| **Lifespan** | `lifespan` в main.py | Инициализация и завершение работы приложения |

---

## Возможность расширения и поддержки кода

- **Модульность**: Каждый компонент в отдельном файле
- **Типизация**: Полные type hints для IDE и статического анализа
- **Документация**: Docstring для всех публичных методов
- **Расширяемость**:
  ```python
  # Новые модели БД
  from app.core import Base
  class User(Base): ...
  
  # Новые методы Redis
  class RedisManager:
      async def get_or_set(self, key, callback): ...
  
  # Новые зависимости
  async def get_user_repo(db = Depends(get_db)): ...

## Управление ресурсами
- **Освобождение**: Все ресурсы закрываются в lifespan при завершении приложения.

## Организация настроек и валидация
- Загрузка из .env через python-dotenv
- Валидация типов и значений.

## Реализация lifecycle приложения 
- **Гарантирует**: инициализацию до запросов, корректное завершение, обработку ошибок.

## Dependency Injection
```python
# Зависимости
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_manager.get_session() as session:
        yield session

async def get_redis() -> Redis:
    return redis_manager.client

# Использование
@app.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    await db.execute(text("SELECT 1"))
    await redis.ping()
```
- **Преимущества**: тестирование, переиспользование, типобезопасность.

## Дальнейшее использование интерфейсов core модуля

```python
# 1. Модели
from app.core import Base

# 2. Репозитории
class UserRepository:
    def __init__(self, db: AsyncSession = Depends(get_db)): ...

# 3. Сервисы с кэшированием
class UserService:
    def __init__(self, db: Depends(get_db), redis: Depends(get_redis)): ...
    async def get_cached_user(self, id): ...

# 4. Эндпоинты
@router.get("/users/{id}")
async def get_user(service: UserService = Depends(get_user_service)): ...
```
## Идеи по улучшению модуля

- Ретраи при временных ошибках подключения
- Circuit breaker для защиты ресурсов
- Метрики (Prometheus) для мониторинга
- Кэширование запросов
- Alembic миграции для управления схемой БД
- Логирование запросов

## Мысли и замечания

**Что получилось хорошо:**
- Чистая архитектура с разделением ответственности
- Правильное управление ресурсами
- Полная async реализация
- Готовность к продакшену

**Компромиссы:**
- Глобальные объекты vs тестирование (решение: DI для бизнес-логики)
- Автосоздание таблиц только для development

**Не вошло в реализацию:**
- Миграции Alembic (требует отдельной настройки)
- Метрики и трассировка
- Тесты (модуль спроектирован для легкого тестирования)