from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.models import Base
from app.db import engine
from app.routers import players, challenges, matches, activity, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Drop and recreate tables (for development only)
    # In production, use Alembic migrations instead

    # Drop tables in reverse dependency order to avoid foreign key constraint errors
    # First drop matches (which depends on players), then players
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS matches CASCADE"))
        conn.execute(
            text("DROP TABLE IF EXISTS events CASCADE")
        )  # Drop old table name if it exists
        conn.execute(text("DROP TABLE IF EXISTS players CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(players.router)
app.include_router(challenges.router)
app.include_router(matches.router)
app.include_router(activity.router)
app.include_router(auth.router)
