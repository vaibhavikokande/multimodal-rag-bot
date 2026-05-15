from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from typing import AsyncGenerator

# Async engine for FastAPI
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_engine_kwargs = {"echo": settings.DEBUG}
if not _is_sqlite:
    _engine_kwargs.update({"pool_pre_ping": True, "pool_size": 20, "max_overflow": 10})
else:
    _engine_kwargs.update({"connect_args": {"check_same_thread": False}})

async_engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic
_sync_kwargs = {"echo": settings.DEBUG}
if not _is_sqlite:
    _sync_kwargs["pool_pre_ping"] = True
sync_engine = create_engine(settings.SYNC_DATABASE_URL, **_sync_kwargs)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from app.db.base import Base  # noqa – triggers model registration
    from app.db.base_class import metadata
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
