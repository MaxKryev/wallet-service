import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WalletOperation(BaseModel):
    """Схема операции изменения баланса"""

    operation_type: Literal["DEPOSIT", "WITHDRAW"]
    amount: Decimal = Field(
        ..., gt=0, description="Сумма должна быть больше 0"
    )

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Decimal) -> Decimal:
        """В сумме не может быть более 2 знаков после запятой"""
        if v.as_tuple().exponent > 2:  # type: ignore[operator]
            raise ValueError(
                "В сумме не может быть более 2 знаков после запятой"
            )
        return v


class WalletResponse(BaseModel):
    """Схема ответа с данными кошелька"""

    id: uuid.UUID
    balance: Decimal

    model_config = ConfigDict(from_attributes=True)
