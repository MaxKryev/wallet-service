from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.db.session import init_db

app = FastAPI(
    title="Wallet Service",
    version="1.0.0",
    contact={"name": "Max Kraev", "email": "kraev-1993@list.ru"},
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
