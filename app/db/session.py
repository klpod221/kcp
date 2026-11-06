import json
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.logging import logger
from app.db.models import Base, OAuthClient, User

# Configure async engine options
engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

async_engine = create_async_engine(settings.DATABASE_URL, echo=False, **engine_args)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an active SQLAlchemy AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initializes tables and seeds default admin user & OAuth client."""
    from app.core.security import hash_password

    logger.info("Initializing database schema...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Seed Default Admin User if not present
        result = await session.execute(
            select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)
        )
        admin_user = result.scalars().first()
        if not admin_user:
            logger.info(f"Seeding default admin user: '{settings.DEFAULT_ADMIN_USERNAME}'")
            admin_user = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                email=settings.DEFAULT_ADMIN_EMAIL,
                is_active=True,
                is_admin=True,
            )
            session.add(admin_user)
            await session.commit()
        else:
            logger.debug(f"Admin user '{settings.DEFAULT_ADMIN_USERNAME}' already exists.")

        # Seed Default OAuth Client (Google Gemini) if not present
        result = await session.execute(
            select(OAuthClient).where(OAuthClient.client_id == settings.DEFAULT_CLIENT_ID)
        )
        gemini_client = result.scalars().first()
        if not gemini_client:
            logger.info(f"Seeding default OAuth client: '{settings.DEFAULT_CLIENT_ID}'")
            gemini_client = OAuthClient(
                client_id=settings.DEFAULT_CLIENT_ID,
                client_secret_hash=hash_password(settings.DEFAULT_CLIENT_SECRET),
                client_name=settings.DEFAULT_CLIENT_NAME,
                redirect_uris_json=json.dumps(settings.DEFAULT_CLIENT_REDIRECT_URIS),
                allowed_scopes="mcp:read mcp:tools",
                is_active=True,
            )
            session.add(gemini_client)
            await session.commit()
        else:
            logger.debug(f"OAuth client '{settings.DEFAULT_CLIENT_ID}' already exists.")

