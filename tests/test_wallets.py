import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.wallet import Wallet
from tests.conftest import _test_session_maker


@pytest.mark.asyncio
async def test_get_wallet_not_found(client: AsyncClient):
    """GET /wallets/{id} — кошелек не найден."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/wallets/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Кошелек с указанным ID не найден"


@pytest.mark.asyncio
async def test_get_wallet_balance(client: AsyncClient):
    """GET /wallets/{id} — успешное получение баланса."""
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("150.50"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(wallet_id)
    assert data["balance"] == "150.50"


@pytest.mark.asyncio
async def test_deposit_operation(client: AsyncClient):
    """POST /operation — успешный депозит."""
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("100.00"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "50.00"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == "150.00"


@pytest.mark.asyncio
async def test_withdraw_operation(client: AsyncClient):
    """POST /operation — успешное снятие средств."""
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("200.00"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "75.50"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == "124.50"


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client: AsyncClient):
    """POST /operation — ошибка при недостатке средств."""
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("50.00"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "100.00"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Недостаточно средств для операции"
    async with _test_session_maker() as session:
        updated = await session.get(Wallet, wallet_id)
        assert updated.balance == Decimal("50.00")


@pytest.mark.asyncio
async def test_invalid_operation_type(client: AsyncClient):
    """POST /operation — невалидный тип операции."""
    async with _test_session_maker() as session:
        wallet = Wallet()
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "INVALID", "amount": "100.00"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_negative_amount(client: AsyncClient):
    """POST /operation — отрицательная сумма (валидация Pydantic)."""
    async with _test_session_maker() as session:
        wallet = Wallet()
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "-100.00"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_withdrawals(client: AsyncClient):
    """
    10 параллельных запросов на снятие денег.
    Проверяем, что сработала блокировка SELECT FOR UPDATE.

    Начальный баланс: 1000
    10 запросов по 100 = 1000
    Ожидаемый финальный баланс: 0
    """
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("1000.00"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    async def withdraw():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": "100.00"},
        )

    tasks = [withdraw() for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert (
            resp.status_code == 200
        ), f"Unexpected status: {resp.status_code}"

    final_response = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final_response.status_code == 200
    assert final_response.json()["balance"] == "0.00"


@pytest.mark.asyncio
async def test_concurrent_deposit_and_withdraw(client: AsyncClient):
    """
    Депозиты и снятия одновременно.
    Начальный баланс: 500
    5 депозитов по 100 = +500
    5 снятий по 100 = -500
    Ожидаемый баланс: 500
    """
    async with _test_session_maker() as session:
        wallet = Wallet(balance=Decimal("500.00"))
        session.add(wallet)
        await session.commit()
        wallet_id = wallet.id

    async def deposit():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "100.00"},
        )

    async def withdraw():
        return await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": "100.00"},
        )

    tasks = [deposit() for _ in range(5)] + [withdraw() for _ in range(5)]
    responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200

    final = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert final.json()["balance"] == "500.00"
