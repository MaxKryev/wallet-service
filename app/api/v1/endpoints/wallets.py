from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.wallet import WalletOperation, WalletResponse
from app.services.wallet import WalletService

router = APIRouter()


@router.post("/wallets/{wallet_id}/operation", response_model=WalletResponse)
async def perform_operation(
    wallet_id: UUID,
    operation: WalletOperation,
    session: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Операции с балансом кошелька"""
    try:
        wallet = await WalletService.process_operation(
            session, str(wallet_id), operation
        )
        return WalletResponse.model_validate(wallet)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_EROR,
            detail=str(e),
        )


@router.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet_balance(
    wallet_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> WalletResponse:
    """Просмотр текущего баланса кошелька"""
    wallet = await WalletService.get_wallet(session, str(wallet_id))
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кошелек с указанным ID не найден",
        )
    return WalletResponse.model_validate(wallet)
