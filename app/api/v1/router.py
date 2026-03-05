from fastapi import APIRouter

from app.api.v1.endpoints import wallets

api_router = APIRouter()
api_router.include_router(wallets.router, tags=["wallets"])
