from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
import mercadopago
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentPreferenceCreate, CardPaymentCreate, PaymentResponse, PaymentPreferenceResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/payment", tags=["payment"])

sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)


@router.get("/public-key")
def get_public_key():
    return {"public_key": settings.MP_PUBLIC_KEY}


@router.post("/preference", response_model=PaymentPreferenceResponse)
def create_preference(
    data: PaymentPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == data.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido nao encontrado"
        )

    if order.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedido ja foi pago"
        )

    items = []
    for item in order.items:
        items.append({
            "title": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "currency_id": "BRL"
        })

    preference_data = {
        "items": items,
        "payer": {
            "name": current_user.name,
            "email": current_user.email
        },
        "back_urls": {
            "success": f"{settings.FRONTEND_URL}/pagamento/sucesso",
            "failure": f"{settings.FRONTEND_URL}/pagamento/falha",
            "pending": f"{settings.FRONTEND_URL}/pagamento/pendente"
        },
        "auto_return": "approved",
        "external_reference": str(order.id),
        "payment_methods": {
            "excluded_payment_types": [],
            "installments": 12
        }
    }

    if data.payment_method == "pix":
        preference_data["payment_methods"]["default_payment_method_id"] = "pix"
    elif data.payment_method == "boleto":
        preference_data["payment_methods"]["default_payment_method_id"] = "bolbradesco"

    preference_response = sdk.preference().create(preference_data)

    if preference_response["status"] != 201:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar preferencia de pagamento"
        )

    preference = preference_response["response"]

    return {
        "preference_id": preference["id"],
        "init_point": preference["init_point"],
        "sandbox_init_point": preference.get("sandbox_init_point")
    }


@router.post("/pix", response_model=PaymentResponse)
def create_pix_payment(
    data: PaymentPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == data.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido nao encontrado"
        )

    if order.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedido ja foi pago"
        )

    payment_data = {
        "transaction_amount": float(order.total),
        "description": f"Pedido #{order.id} - Aprova Facil",
        "payment_method_id": "pix",
        "payer": {
            "email": current_user.email,
            "first_name": current_user.name.split()[0] if current_user.name else "Cliente",
            "last_name": current_user.name.split()[-1] if current_user.name and len(current_user.name.split()) > 1 else ""
        }
    }

    if current_user.cpf:
        payment_data["payer"]["identification"] = {
            "type": "CPF",
            "number": current_user.cpf.replace(".", "").replace("-", "")
        }

    payment_response = sdk.payment().create(payment_data)

    if payment_response["status"] not in [200, 201]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar pagamento PIX"
        )

    mp_payment = payment_response["response"]

    payment = Payment(
        order_id=order.id,
        mp_payment_id=str(mp_payment["id"]),
        method="pix",
        status=mp_payment["status"],
        amount=order.total,
        pix_qr_code=mp_payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code"),
        pix_qr_code_base64=mp_payment.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64")
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@router.post("/card", response_model=PaymentResponse)
def create_card_payment(
    data: CardPaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == data.order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido nao encontrado"
        )

    if order.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pedido ja foi pago"
        )

    payment_data = {
        "transaction_amount": float(order.total),
        "token": data.token,
        "description": f"Pedido #{order.id} - Aprova Facil",
        "installments": data.installments,
        "payment_method_id": data.payment_method_id,
        "payer": {
            "email": current_user.email
        }
    }

    if data.issuer_id:
        payment_data["issuer_id"] = data.issuer_id

    payment_response = sdk.payment().create(payment_data)

    if payment_response["status"] not in [200, 201]:
        error_message = payment_response.get("response", {}).get("message", "Erro ao processar pagamento")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    mp_payment = payment_response["response"]

    payment = Payment(
        order_id=order.id,
        mp_payment_id=str(mp_payment["id"]),
        method="card",
        status=mp_payment["status"],
        amount=order.total
    )

    db.add(payment)

    if mp_payment["status"] == "approved":
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        payment.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(payment)

    return payment


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.json()

    if body.get("type") == "payment":
        payment_id = body.get("data", {}).get("id")

        if payment_id:
            payment_info = sdk.payment().get(payment_id)

            if payment_info["status"] == 200:
                mp_payment = payment_info["response"]
                external_reference = mp_payment.get("external_reference")

                if external_reference:
                    order = db.query(Order).filter(Order.id == int(external_reference)).first()

                    if order:
                        payment = db.query(Payment).filter(Payment.order_id == order.id).first()

                        if payment:
                            payment.status = mp_payment["status"]

                            if mp_payment["status"] == "approved":
                                order.status = "paid"
                                order.paid_at = datetime.utcnow()
                                payment.paid_at = datetime.utcnow()

                            db.commit()

    return {"status": "ok"}


@router.get("/status/{order_id}", response_model=PaymentResponse)
def get_payment_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido nao encontrado"
        )

    payment = db.query(Payment).filter(Payment.order_id == order_id).order_by(Payment.created_at.desc()).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento nao encontrado"
        )

    return payment
