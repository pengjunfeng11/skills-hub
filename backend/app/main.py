from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from app.config import settings
from app.core.security import hash_password
from app.database import async_session, engine, Base
from app.models import *  # noqa: F401, F403 - ensure all models are loaded


async def create_default_admin():
    """Create default admin user if no users exist."""
    async with async_session() as db:
        count = (await db.execute(select(func.count()).select_from(User))).scalar()
        if count == 0:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password_hash=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.TESTING:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await create_default_admin()
    yield


app = FastAPI(title="Skills Hub", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.auth import router as auth_router
from app.api.skills import router as skills_router
from app.api.teams import router as teams_router
from app.api.plugin import router as plugin_router
from app.api.admin import router as admin_router

app.include_router(auth_router)
app.include_router(skills_router)
app.include_router(teams_router)
app.include_router(plugin_router)
app.include_router(admin_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
