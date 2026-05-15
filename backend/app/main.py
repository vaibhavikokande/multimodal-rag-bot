"""
Multimodal Enterprise RAG Bot - FastAPI Backend
"""
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    from app.db.session import init_db
    await init_db()
    logger.info("Database initialized")

    # Seed admin user
    await seed_admin()

    yield

    logger.info("Shutting down...")


async def seed_admin():
    """Create default admin user if not exists"""
    from app.db.session import AsyncSessionLocal
    from app.crud.user import get_user_by_email, create_user
    from app.core.security import get_password_hash

    async with AsyncSessionLocal() as db:
        existing = await get_user_by_email(db, settings.ADMIN_EMAIL)
        if not existing:
            await create_user(
                db=db,
                email=settings.ADMIN_EMAIL,
                full_name="System Admin",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role="superadmin",
                is_active=True,
                is_verified=True,
            )
            logger.info(f"Admin user created: {settings.ADMIN_EMAIL}")


# Initialize Sentry
if settings.SENTRY_DSN and sentry_sdk:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Multimodal RAG Platform API",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }
