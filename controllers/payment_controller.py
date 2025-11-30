from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import verify_api_key
from schemas.payment import PaymentRequest, PreferenceRequest
from services.mercadopago_service import MercadoPagoService, get_mercadopago_service
from services.payment_service import PaymentService

router = APIRouter(prefix="/api/payment", tags=["Payment"])


def get_payment_service(
    db: AsyncSession = Depends(get_db),
    mp_service: MercadoPagoService = Depends(get_mercadopago_service)
) -> PaymentService:
    return PaymentService(db, mp_service)


@router.get("/public-key", dependencies=[Depends(verify_api_key)])
async def get_public_key(
    mp_service: MercadoPagoService = Depends(get_mercadopago_service)
):
    """Retorna a public key do Mercado Pago para inicializar os Bricks"""
    return {"public_key": mp_service.get_public_key()}


@router.post("/process", dependencies=[Depends(verify_api_key)])
async def process_payment(
    payment: PaymentRequest,
    service: PaymentService = Depends(get_payment_service)
):
    """Processa um pagamento via Card Payment Brick"""
    result = await service.process_payment(payment)

    if not result.get("success"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("error")
        )

    return result


@router.post("/preference", dependencies=[Depends(verify_api_key)])
async def create_preference(
    preference: PreferenceRequest,
    service: PaymentService = Depends(get_payment_service)
):
    """Cria uma preferência para Payment Brick ou Checkout Pro"""
    result = await service.create_preference(preference)

    if not result.get("success"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("error")
        )

    return result


@router.get("/methods", dependencies=[Depends(verify_api_key)])
async def get_payment_methods(
    service: PaymentService = Depends(get_payment_service)
):
    """Retorna os métodos de pagamento disponíveis"""
    return service.get_payment_methods()


@router.get("/installments", dependencies=[Depends(verify_api_key)])
async def get_installments(
    amount: float,
    bin: str,
    service: PaymentService = Depends(get_payment_service)
):
    """Retorna as opções de parcelamento para um valor e BIN do cartão"""
    return service.get_installments(amount, bin)


@router.get("/{payment_id}", dependencies=[Depends(verify_api_key)])
async def get_payment(
    payment_id: str,
    service: PaymentService = Depends(get_payment_service)
):
    """Busca informações de um pagamento pelo ID"""
    result = await service.get_payment(payment_id)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Payment not found")

    return result


@router.post("/webhook")
async def webhook(
    request: Request,
    service: PaymentService = Depends(get_payment_service)
):
    """Recebe notificações de webhook do Mercado Pago (sem autenticação)"""
    try:
        body = await request.json()
        result = await service.handle_webhook(body)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
