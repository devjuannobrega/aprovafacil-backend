from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import verify_api_key
from schemas.payment import (
    PaymentRequest,
    PreferenceRequest,
    PublicKeyResponse,
    PaymentSuccessResponse,
    PreferenceSuccessResponse,
    PaymentInfoResponse,
    WebhookResponse,
    ErrorResponse,
)
from services.mercadopago_service import MercadoPagoService, get_mercadopago_service
from services.payment_service import PaymentService

router = APIRouter(
    prefix="/api/payment",
    tags=["Payment"],
    responses={
        401: {"model": ErrorResponse, "description": "API Key inválida ou ausente"},
        500: {"model": ErrorResponse, "description": "Erro interno do servidor"},
    }
)


def get_payment_service(
    db: AsyncSession = Depends(get_db),
    mp_service: MercadoPagoService = Depends(get_mercadopago_service)
) -> PaymentService:
    return PaymentService(db, mp_service)


@router.get(
    "/public-key",
    dependencies=[Depends(verify_api_key)],
    response_model=PublicKeyResponse,
    summary="Obter Public Key",
    description="""
Retorna a public key do Mercado Pago necessária para inicializar os Bricks no frontend.

**Uso no frontend:**
```javascript
const mp = new MercadoPago('PUBLIC_KEY_RETORNADA');
```

Esta chave é segura para exposição no frontend e identifica sua conta Mercado Pago.
    """,
    responses={
        200: {
            "description": "Public key retornada com sucesso",
            "model": PublicKeyResponse,
        }
    }
)
async def get_public_key(
    mp_service: MercadoPagoService = Depends(get_mercadopago_service)
):
    return {"public_key": mp_service.get_public_key()}


@router.post(
    "/process",
    dependencies=[Depends(verify_api_key)],
    response_model=PaymentSuccessResponse,
    summary="Processar Pagamento",
    description="""
Processa um pagamento com cartão de crédito/débito utilizando o token gerado pelo Card Payment Brick.

**Fluxo de uso:**
1. No frontend, o Card Payment Brick coleta os dados do cartão
2. O Brick gera um `token` seguro (dados do cartão nunca chegam ao seu servidor)
3. Envie o token junto com os dados do pagamento para este endpoint
4. A API processa o pagamento no Mercado Pago e retorna o resultado

**Status possíveis na resposta:**
- `approved`: Pagamento aprovado
- `pending`: Pagamento pendente (aguardando ação do comprador)
- `rejected`: Pagamento rejeitado

**Importante:** O token gerado pelo Brick expira em 7 dias ou após o primeiro uso.
    """,
    responses={
        200: {
            "description": "Pagamento processado com sucesso",
            "model": PaymentSuccessResponse,
        },
        400: {
            "description": "Dados inválidos ou pagamento rejeitado",
            "model": ErrorResponse,
        }
    }
)
async def process_payment(
    payment: PaymentRequest,
    service: PaymentService = Depends(get_payment_service)
):
    result = await service.process_payment(payment)

    if not result.get("success"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("error")
        )

    return result


@router.post(
    "/preference",
    dependencies=[Depends(verify_api_key)],
    response_model=PreferenceSuccessResponse,
    summary="Criar Preferência de Pagamento",
    description="""
Cria uma preferência de pagamento no Mercado Pago para usar com Payment Brick ou Checkout Pro.

**O que é uma preferência?**
Uma preferência contém todas as informações do pedido (itens, valores, dados do pagador)
e retorna URLs para redirecionar o cliente ao checkout do Mercado Pago.

**Casos de uso:**
- **Checkout Pro**: Redireciona o cliente para a página do Mercado Pago
- **Payment Brick**: Usa o `preference_id` para inicializar o Brick

**URLs retornadas:**
- `init_point`: URL de produção (pagamentos reais)
- `sandbox_init_point`: URL de sandbox (testes)

**Dica:** Use `external_reference` para identificar o pedido no seu sistema e facilitar a reconciliação.
    """,
    responses={
        200: {
            "description": "Preferência criada com sucesso",
            "model": PreferenceSuccessResponse,
        },
        400: {
            "description": "Dados inválidos",
            "model": ErrorResponse,
        }
    }
)
async def create_preference(
    preference: PreferenceRequest,
    service: PaymentService = Depends(get_payment_service)
):
    result = await service.create_preference(preference)

    if not result.get("success"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail=result.get("error")
        )

    return result


@router.get(
    "/methods",
    dependencies=[Depends(verify_api_key)],
    summary="Listar Métodos de Pagamento",
    description="""
Retorna todos os métodos de pagamento disponíveis na sua conta Mercado Pago.

**Métodos comuns retornados:**
- Cartões de crédito: Visa, Mastercard, American Express, Elo, Hipercard
- Cartões de débito: Visa Débito, Mastercard Débito, Elo Débito
- Outros: Pix, Boleto bancário

**Uso típico:**
Utilize esta lista para exibir os métodos aceitos no seu frontend ou para validar
o `payment_method_id` antes de processar um pagamento.

Cada método inclui `thumbnail` e `secure_thumbnail` com ícones para exibição.
    """,
    responses={
        200: {
            "description": "Lista de métodos de pagamento",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "methods": [
                            {"id": "visa", "name": "Visa", "payment_type_id": "credit_card"},
                            {"id": "master", "name": "Mastercard", "payment_type_id": "credit_card"},
                            {"id": "pix", "name": "Pix", "payment_type_id": "bank_transfer"}
                        ]
                    }
                }
            }
        }
    }
)
async def get_payment_methods(
    service: PaymentService = Depends(get_payment_service)
):
    return service.get_payment_methods()


@router.get(
    "/installments",
    dependencies=[Depends(verify_api_key)],
    summary="Consultar Parcelamento",
    description="""
Retorna as opções de parcelamento disponíveis para um valor e BIN do cartão.

**O que é BIN?**
BIN (Bank Identification Number) são os primeiros 6-8 dígitos do cartão.
Ele identifica o banco emissor e determina as opções de parcelamento.

**Parâmetros:**
- `amount`: Valor total da compra (ex: 150.00)
- `bin`: Primeiros 6 dígitos do cartão (ex: 411111)

**Resposta:**
Cada opção de parcelamento inclui:
- Número de parcelas
- Valor de cada parcela
- Valor total (com juros, se houver)
- Taxa de juros aplicada
- Mensagem formatada para exibição (ex: "3x R$ 50,00 sem juros")

**Uso típico:**
Chame este endpoint quando o usuário digitar os primeiros 6 dígitos do cartão
para exibir as opções de parcelamento em tempo real.
    """,
    responses={
        200: {
            "description": "Opções de parcelamento disponíveis",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "payment_method_id": "visa",
                        "issuer_id": "24",
                        "payer_costs": [
                            {"installments": 1, "installment_amount": 150.0, "total_amount": 150.0, "installment_rate": 0, "recommended_message": "1x R$ 150,00 sem juros"},
                            {"installments": 3, "installment_amount": 50.0, "total_amount": 150.0, "installment_rate": 0, "recommended_message": "3x R$ 50,00 sem juros"}
                        ]
                    }
                }
            }
        }
    }
)
async def get_installments(
    amount: float = Query(
        ...,
        description="Valor total da compra em reais",
        gt=0,
        examples=[150.00]
    ),
    bin: str = Query(
        ...,
        description="Primeiros 6 dígitos do cartão (BIN)",
        min_length=6,
        max_length=8,
        examples=["411111"]
    ),
    service: PaymentService = Depends(get_payment_service)
):
    return service.get_installments(amount, bin)


@router.get(
    "/{payment_id}",
    dependencies=[Depends(verify_api_key)],
    response_model=PaymentInfoResponse,
    summary="Consultar Pagamento",
    description="""
Busca informações detalhadas de um pagamento pelo ID do Mercado Pago.

**Informações retornadas:**
- Status atual do pagamento
- Valor e método de pagamento
- Dados do pagador
- Datas de criação e aprovação
- Detalhes de parcelas (se aplicável)

**Casos de uso:**
- Verificar status de um pagamento específico
- Exibir detalhes do pagamento para o cliente
- Reconciliação de pagamentos

**Dica:** Use o `external_reference` para encontrar pagamentos pelo ID do seu sistema.
    """,
    responses={
        200: {
            "description": "Dados do pagamento encontrado",
            "model": PaymentInfoResponse,
        },
        404: {
            "description": "Pagamento não encontrado",
            "model": ErrorResponse,
        }
    }
)
async def get_payment(
    payment_id: str = Path(
        ...,
        description="ID do pagamento no Mercado Pago",
        examples=["1234567890"]
    ),
    service: PaymentService = Depends(get_payment_service)
):
    result = await service.get_payment(payment_id)

    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")

    return result


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Webhook do Mercado Pago",
    description="""
Endpoint para receber notificações de webhook do Mercado Pago.

**Este endpoint NÃO requer autenticação** pois é chamado diretamente pelo Mercado Pago.

**Eventos recebidos:**
- `payment.created`: Novo pagamento criado
- `payment.updated`: Status do pagamento alterado

**Configuração:**
Configure esta URL no painel do Mercado Pago:
1. Acesse: Suas integrações > [Sua aplicação] > Webhooks
2. Adicione a URL: `https://seudominio.com/api/payment/webhook`
3. Selecione os eventos que deseja receber

**Importante:**
- O Mercado Pago espera resposta HTTP 200/201 em até 500ms
- Se não receber resposta, ele reenviará a notificação
- Sempre retorne sucesso mesmo se houver erro no processamento interno
    """,
    responses={
        200: {
            "description": "Webhook recebido com sucesso",
            "model": WebhookResponse,
        }
    },
    tags=["Webhook"]
)
async def webhook(
    request: Request,
    service: PaymentService = Depends(get_payment_service)
):
    try:
        body = await request.json()
        result = await service.handle_webhook(body)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}
