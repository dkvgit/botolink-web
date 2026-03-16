# core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Получаем строку подключения из .env или используем локальную БД
# Пример: DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres@localhost/botolinkpro")

# Создаем движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Логировать SQL запросы (для разработки)
    future=True
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

# Функция для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# core/database.py

# Создаем движок с фиксом для PgBouncer
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # Добавляем эти параметры, чтобы убрать ошибку prepared statement
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)