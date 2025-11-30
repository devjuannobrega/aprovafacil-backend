from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.transaction import Transaction
from repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def get_by_mp_payment_id(self, mp_payment_id: str) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.mp_payment_id == mp_payment_id)
        )
        return list(result.scalars().all())

    async def get_by_action(self, action: str) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.action == action)
        )
        return list(result.scalars().all())
