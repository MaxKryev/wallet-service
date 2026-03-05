from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.schemas.wallet import WalletOperation


class WalletService:
    """Сервис для работы с кошельками"""

    @staticmethod
    async def get_wallet(
        session: AsyncSession, wallet_id: str
    ) -> Wallet | None:
        """Получаем кошелек по ID"""
        result = await session.execute(
            select(Wallet).where(Wallet.id == wallet_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def process_operation(
        session: AsyncSession, wallet_id: str, operation: WalletOperation
    ) -> Wallet:
        """Обработка операции изменения баланса"""
        select_wallet = (
            select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        )

        result = await session.execute(select_wallet)
        wallet = result.scalar_one_or_none()

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Кошелек с указанным ID не найден",
            )

        if operation.operation_type == "DEPOSIT":
            wallet.balance += operation.amount  # type: ignore[assignment]
        elif operation.operation_type == "WITHDRAW":

            if wallet.balance < operation.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Недостаточно средств для операции",
                )
            wallet.balance -= operation.amount  # type: ignore[assignment]

        await session.commit()
        await session.refresh(wallet)
        return wallet
