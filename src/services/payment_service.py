from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment import Payment
from src.models.transaction import Transaction
from src.repositories.payment_repository import PaymentRepository
from src.repositories.transaction_repository import TransactionRepository
from src.schemas.payment import PaymentRequest, PreferenceRequest
from src.services.mercadopago_service import MercadoPagoService


class PaymentService:
    def __init__(self, session: AsyncSession, mp_service: MercadoPagoService):
        self.session = session
        self.mp_service = mp_service
        self.payment_repo = PaymentRepository(session)
        self.transaction_repo = TransactionRepository(session)

    async def process_payment(self, payment_request: PaymentRequest) -> dict:
        transaction = Transaction(
            action="create_payment",
            request_payload=payment_request.model_dump(),
            status="pending"
        )
        await self.transaction_repo.create(transaction)

        result = self.mp_service.create_payment(payment_request)

        if result["status"] == 201:
            response = result["response"]

            payment = Payment(
                mp_payment_id=str(response["id"]),
                status=response["status"],
                status_detail=response.get("status_detail"),
                transaction_amount=response["transaction_amount"],
                installments=response.get("installments", 1),
                payment_method_id=response["payment_method_id"],
                payment_type_id=response.get("payment_type_id"),
                payer_email=payment_request.payer.email,
                payer_identification_type=payment_request.payer.identification.type if payment_request.payer.identification else None,
                payer_identification_number=payment_request.payer.identification.number if payment_request.payer.identification else None,
                external_reference=payment_request.external_reference,
                description=payment_request.description,
            )
            await self.payment_repo.create(payment)

            transaction.mp_payment_id = str(response["id"])
            transaction.response_payload = response
            transaction.status = "success"
            await self.transaction_repo.update(transaction)

            return {
                "success": True,
                "payment_id": response["id"],
                "status": response["status"],
                "status_detail": response.get("status_detail"),
            }
        else:
            transaction.response_payload = result.get("response")
            transaction.status = "error"
            transaction.error_message = str(result.get("response"))
            await self.transaction_repo.update(transaction)

            return {
                "success": False,
                "error": result.get("response"),
                "status_code": result["status"],
            }

    async def create_preference(self, preference_request: PreferenceRequest) -> dict:
        transaction = Transaction(
            action="create_preference",
            request_payload=preference_request.model_dump(),
            status="pending"
        )
        await self.transaction_repo.create(transaction)

        result = self.mp_service.create_preference(preference_request)

        if result["status"] == 201:
            response = result["response"]

            transaction.response_payload = response
            transaction.status = "success"
            await self.transaction_repo.update(transaction)

            return {
                "success": True,
                "preference_id": response["id"],
                "init_point": response["init_point"],
                "sandbox_init_point": response["sandbox_init_point"],
            }
        else:
            transaction.response_payload = result.get("response")
            transaction.status = "error"
            transaction.error_message = str(result.get("response"))
            await self.transaction_repo.update(transaction)

            return {
                "success": False,
                "error": result.get("response"),
                "status_code": result["status"],
            }

    async def handle_webhook(self, payload: dict) -> dict:
        transaction = Transaction(
            action="webhook",
            request_payload=payload,
            status="received"
        )

        if payload.get("type") == "payment":
            payment_id = payload.get("data", {}).get("id")
            if payment_id:
                transaction.mp_payment_id = str(payment_id)

                result = self.mp_service.get_payment(str(payment_id))
                if result["status"] == 200:
                    response = result["response"]

                    await self.payment_repo.update_status(
                        mp_payment_id=str(payment_id),
                        status=response["status"],
                        status_detail=response.get("status_detail", "")
                    )

                    transaction.response_payload = response
                    transaction.status = "processed"
                else:
                    transaction.status = "error"
                    transaction.error_message = str(result.get("response"))

        await self.transaction_repo.create(transaction)
        return {"status": "ok"}

    async def get_payment(self, payment_id: str) -> dict:
        payment = await self.payment_repo.get_by_mp_payment_id(payment_id)

        if payment:
            return {
                "success": True,
                "payment": {
                    "id": payment.id,
                    "mp_payment_id": payment.mp_payment_id,
                    "status": payment.status,
                    "status_detail": payment.status_detail,
                    "transaction_amount": payment.transaction_amount,
                    "installments": payment.installments,
                    "payment_method_id": payment.payment_method_id,
                    "payer_email": payment.payer_email,
                    "created_at": payment.created_at.isoformat(),
                }
            }

        result = self.mp_service.get_payment(payment_id)
        if result["status"] == 200:
            return {"success": True, "payment": result["response"]}

        return {"success": False, "error": "Payment not found"}

    def get_payment_methods(self) -> dict:
        result = self.mp_service.get_payment_methods()
        return result["response"]

    def get_installments(self, amount: float, bin: str) -> dict:
        result = self.mp_service.get_installments(amount, bin)
        return result["response"]
