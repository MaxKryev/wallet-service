import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

_TEST_DATABASE_URL = settings.database_url

_test_engine = create_async_engine(
    _TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

_test_session_maker = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db():
    """
    PostgreSQL-совместимая очистка БД перед каждым тестом.
    """
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _test_engine.begin() as conn:
        await conn.execute(
            text("TRUNCATE TABLE wallets RESTART IDENTITY CASCADE")
        )

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """
    HTTP-клиент для тестирования API.
    Подменяет зависимость get_db на тестовую сессию.
    """

    async def override_get_db():
        async with _test_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def db_session():
    """Фикстура для прямого доступа к БД внутри теста."""
    async with _test_session_maker() as session:
        yield session
