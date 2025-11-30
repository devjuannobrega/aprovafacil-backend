from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import Payment
from repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)

    async def get_by_mp_payment_id(self, mp_payment_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.mp_payment_id == mp_payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_external_reference(self, external_reference: str) -> list[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.external_reference == external_reference)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.status == status)
        )
        return list(result.scalars().all())

    async def update_status(self, mp_payment_id: str, status: str, status_detail: str) -> Optional[Payment]:
        payment = await self.get_by_mp_payment_id(mp_payment_id)
        if payment:
            payment.status = status
            payment.status_detail = status_detail
            await self.session.commit()
            await self.session.refresh(payment)
        return payment
