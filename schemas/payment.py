from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime


# ============================================
# Schemas de Identificação e Pagador
# ============================================

class PayerIdentification(BaseModel):
    """Documento de identificação do pagador"""
    type: str = Field(
        ...,
        description="Tipo do documento (CPF, CNPJ)",
        examples=["CPF"]
    )
    number: str = Field(
        ...,
        description="Número do documento sem pontuação",
        examples=["12345678909"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "CPF",
                "number": "12345678909"
            }
        }
    }


class Payer(BaseModel):
    """Informações do pagador"""
    email: EmailStr = Field(
        ...,
        description="E-mail do pagador",
        examples=["cliente@email.com"]
    )
    first_name: Optional[str] = Field(
        None,
        description="Primeiro nome do pagador",
        examples=["João"]
    )
    last_name: Optional[str] = Field(
        None,
        description="Sobrenome do pagador",
        examples=["Silva"]
    )
    identification: Optional[PayerIdentification] = Field(
        None,
        description="Documento de identificação do pagador"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "cliente@email.com",
                "first_name": "João",
                "last_name": "Silva",
                "identification": {
                    "type": "CPF",
                    "number": "12345678909"
                }
            }
        }
    }


# ============================================
# Schemas de Pagamento
# ============================================

class PaymentRequest(BaseModel):
    """Requisição para processar pagamento via Card Payment Brick"""
    token: str = Field(
        ...,
        description="Token do cartão gerado pelo Mercado Pago Bricks",
        examples=["ae37d6b0d7b9b6e2c8e3e0f4a5b6c7d8"]
    )
    transaction_amount: float = Field(
        ...,
        description="Valor total da transação em reais",
        gt=0,
        examples=[150.00]
    )
    installments: int = Field(
        ...,
        description="Número de parcelas (1 = à vista)",
        ge=1,
        le=12,
        examples=[1]
    )
    payment_method_id: str = Field(
        ...,
        description="ID do método de pagamento (visa, master, pix, bolbradesco, etc)",
        examples=["visa"]
    )
    issuer_id: Optional[str] = Field(
        None,
        description="ID do banco emissor do cartão",
        examples=["24"]
    )
    payer: Payer = Field(
        ...,
        description="Dados do pagador"
    )
    description: Optional[str] = Field(
        None,
        description="Descrição do pagamento que aparece na fatura",
        examples=["Compra na Loja XYZ"]
    )
    external_reference: Optional[str] = Field(
        None,
        description="Referência externa para identificar o pedido no seu sistema",
        examples=["PEDIDO-12345"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "ae37d6b0d7b9b6e2c8e3e0f4a5b6c7d8",
                "transaction_amount": 150.00,
                "installments": 1,
                "payment_method_id": "visa",
                "issuer_id": "24",
                "payer": {
                    "email": "cliente@email.com",
                    "first_name": "João",
                    "last_name": "Silva",
                    "identification": {
                        "type": "CPF",
                        "number": "12345678909"
                    }
                },
                "description": "Compra na Loja XYZ",
                "external_reference": "PEDIDO-12345"
            }
        }
    }


class PaymentResponse(BaseModel):
    """Resposta do processamento de pagamento"""
    id: int = Field(..., description="ID interno do pagamento")
    mp_payment_id: str = Field(..., description="ID do pagamento no Mercado Pago")
    status: str = Field(
        ...,
        description="Status do pagamento (approved, pending, rejected, etc)"
    )
    status_detail: Optional[str] = Field(
        None,
        description="Detalhe do status (accredited, pending_contingency, cc_rejected_other_reason, etc)"
    )
    transaction_amount: float = Field(..., description="Valor da transação")
    installments: int = Field(..., description="Número de parcelas")
    payment_method_id: str = Field(..., description="Método de pagamento utilizado")
    payer_email: str = Field(..., description="E-mail do pagador")
    created_at: datetime = Field(..., description="Data/hora de criação")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "mp_payment_id": "1234567890",
                "status": "approved",
                "status_detail": "accredited",
                "transaction_amount": 150.00,
                "installments": 1,
                "payment_method_id": "visa",
                "payer_email": "cliente@email.com",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }


# ============================================
# Schemas de Preferência (Checkout)
# ============================================

class PreferenceItem(BaseModel):
    """Item da preferência de pagamento"""
    id: Optional[str] = Field(
        None,
        description="ID único do item/produto",
        examples=["PROD-001"]
    )
    title: str = Field(
        ...,
        description="Nome/título do produto",
        examples=["Camiseta Básica"]
    )
    description: Optional[str] = Field(
        None,
        description="Descrição detalhada do produto",
        examples=["Camiseta 100% algodão, tamanho M"]
    )
    quantity: int = Field(
        ...,
        description="Quantidade de itens",
        ge=1,
        examples=[2]
    )
    unit_price: float = Field(
        ...,
        description="Preço unitário em reais",
        gt=0,
        examples=[49.90]
    )
    currency_id: str = Field(
        "BRL",
        description="Código da moeda (BRL para Real)",
        examples=["BRL"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "PROD-001",
                "title": "Camiseta Básica",
                "description": "Camiseta 100% algodão, tamanho M",
                "quantity": 2,
                "unit_price": 49.90,
                "currency_id": "BRL"
            }
        }
    }


class PreferenceRequest(BaseModel):
    """Requisição para criar preferência de pagamento (Checkout Pro/Payment Brick)"""
    items: List[PreferenceItem] = Field(
        ...,
        description="Lista de itens do pedido",
        min_length=1
    )
    payer: Optional[Payer] = Field(
        None,
        description="Dados do pagador (opcional, pré-preenche no checkout)"
    )
    external_reference: Optional[str] = Field(
        None,
        description="Referência externa para identificar o pedido",
        examples=["PEDIDO-12345"]
    )
    notification_url: Optional[str] = Field(
        None,
        description="URL para receber notificações de webhook",
        examples=["https://seusite.com/api/payment/webhook"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {
                        "id": "PROD-001",
                        "title": "Camiseta Básica",
                        "description": "Camiseta 100% algodão, tamanho M",
                        "quantity": 2,
                        "unit_price": 49.90,
                        "currency_id": "BRL"
                    },
                    {
                        "id": "PROD-002",
                        "title": "Calça Jeans",
                        "quantity": 1,
                        "unit_price": 129.90,
                        "currency_id": "BRL"
                    }
                ],
                "payer": {
                    "email": "cliente@email.com",
                    "first_name": "João",
                    "last_name": "Silva"
                },
                "external_reference": "PEDIDO-12345",
                "notification_url": "https://seusite.com/api/payment/webhook"
            }
        }
    }


class PreferenceResponse(BaseModel):
    """Resposta da criação de preferência"""
    preference_id: str = Field(
        ...,
        description="ID da preferência gerada pelo Mercado Pago"
    )
    init_point: str = Field(
        ...,
        description="URL do checkout de produção"
    )
    sandbox_init_point: str = Field(
        ...,
        description="URL do checkout para testes (sandbox)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "preference_id": "1234567890-abcdef12-3456-7890",
                "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=1234567890",
                "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=1234567890"
            }
        }
    }


# ============================================
# Schemas de Webhook
# ============================================

class WebhookPayload(BaseModel):
    """Payload recebido nas notificações de webhook do Mercado Pago"""
    action: Optional[str] = Field(
        None,
        description="Ação que disparou o webhook (payment.created, payment.updated, etc)",
        examples=["payment.updated"]
    )
    api_version: Optional[str] = Field(
        None,
        description="Versão da API do Mercado Pago",
        examples=["v1"]
    )
    data: Optional[dict] = Field(
        None,
        description="Dados do evento (contém o ID do pagamento)",
        examples=[{"id": "1234567890"}]
    )
    date_created: Optional[str] = Field(
        None,
        description="Data de criação do evento",
        examples=["2024-01-15T10:30:00.000-03:00"]
    )
    id: Optional[int] = Field(
        None,
        description="ID único do evento de webhook",
        examples=[12345678901]
    )
    live_mode: Optional[bool] = Field(
        None,
        description="Indica se é ambiente de produção (true) ou sandbox (false)",
        examples=[True]
    )
    type: Optional[str] = Field(
        None,
        description="Tipo do recurso (payment, merchant_order, etc)",
        examples=["payment"]
    )
    user_id: Optional[str] = Field(
        None,
        description="ID do usuário do Mercado Pago que recebeu o pagamento",
        examples=["123456789"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "action": "payment.updated",
                "api_version": "v1",
                "data": {"id": "1234567890"},
                "date_created": "2024-01-15T10:30:00.000-03:00",
                "id": 12345678901,
                "live_mode": True,
                "type": "payment",
                "user_id": "123456789"
            }
        }
    }


# ============================================
# Schemas de Resposta da API
# ============================================

class PublicKeyResponse(BaseModel):
    """Resposta contendo a public key do Mercado Pago"""
    public_key: str = Field(
        ...,
        description="Public key para inicializar os Bricks no frontend"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "public_key": "APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            }
        }
    }


class PaymentMethodInfo(BaseModel):
    """Informações de um método de pagamento"""
    id: str = Field(..., description="ID do método", examples=["visa"])
    name: str = Field(..., description="Nome do método", examples=["Visa"])
    payment_type_id: str = Field(..., description="Tipo do pagamento", examples=["credit_card"])
    thumbnail: str = Field(..., description="URL do ícone do método")
    secure_thumbnail: str = Field(..., description="URL segura (HTTPS) do ícone")


class PaymentMethodsResponse(BaseModel):
    """Lista de métodos de pagamento disponíveis"""
    success: bool = Field(..., description="Indica se a requisição foi bem sucedida")
    methods: List[PaymentMethodInfo] = Field(..., description="Lista de métodos disponíveis")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "methods": [
                    {
                        "id": "visa",
                        "name": "Visa",
                        "payment_type_id": "credit_card",
                        "thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/0daa1670-5c81-11ec-ae75-df2bef173be2-xl@2x.png",
                        "secure_thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/0daa1670-5c81-11ec-ae75-df2bef173be2-xl@2x.png"
                    },
                    {
                        "id": "master",
                        "name": "Mastercard",
                        "payment_type_id": "credit_card",
                        "thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/aa2b8f70-5c85-11ec-ae75-df2bef173be2-xl@2x.png",
                        "secure_thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/aa2b8f70-5c85-11ec-ae75-df2bef173be2-xl@2x.png"
                    },
                    {
                        "id": "pix",
                        "name": "Pix",
                        "payment_type_id": "bank_transfer",
                        "thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/pix-xl@2x.png",
                        "secure_thumbnail": "https://http2.mlstatic.com/storage/logos-api-admin/pix-xl@2x.png"
                    }
                ]
            }
        }
    }


class InstallmentOption(BaseModel):
    """Opção de parcelamento"""
    installments: int = Field(..., description="Número de parcelas", examples=[3])
    installment_amount: float = Field(..., description="Valor de cada parcela", examples=[50.00])
    total_amount: float = Field(..., description="Valor total com juros", examples=[150.00])
    installment_rate: float = Field(..., description="Taxa de juros (%)", examples=[0.0])
    recommended_message: str = Field(
        ...,
        description="Mensagem formatada para exibir",
        examples=["3x R$ 50,00 sem juros"]
    )


class InstallmentsResponse(BaseModel):
    """Resposta das opções de parcelamento"""
    success: bool = Field(..., description="Indica se a requisição foi bem sucedida")
    payment_method_id: str = Field(..., description="Método de pagamento consultado")
    issuer_id: Optional[str] = Field(None, description="ID do banco emissor")
    payer_costs: List[InstallmentOption] = Field(..., description="Opções de parcelamento")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "payment_method_id": "visa",
                "issuer_id": "24",
                "payer_costs": [
                    {
                        "installments": 1,
                        "installment_amount": 150.00,
                        "total_amount": 150.00,
                        "installment_rate": 0.0,
                        "recommended_message": "1x R$ 150,00 sem juros"
                    },
                    {
                        "installments": 3,
                        "installment_amount": 50.00,
                        "total_amount": 150.00,
                        "installment_rate": 0.0,
                        "recommended_message": "3x R$ 50,00 sem juros"
                    },
                    {
                        "installments": 6,
                        "installment_amount": 26.50,
                        "total_amount": 159.00,
                        "installment_rate": 6.0,
                        "recommended_message": "6x R$ 26,50 (R$ 159,00)"
                    }
                ]
            }
        }
    }


class PaymentSuccessResponse(BaseModel):
    """Resposta de sucesso do processamento de pagamento"""
    success: bool = Field(True, description="Indica sucesso na operação")
    payment_id: str = Field(..., description="ID do pagamento no Mercado Pago")
    status: str = Field(..., description="Status do pagamento")
    status_detail: str = Field(..., description="Detalhe do status")
    external_reference: Optional[str] = Field(None, description="Referência externa")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "payment_id": "1234567890",
                "status": "approved",
                "status_detail": "accredited",
                "external_reference": "PEDIDO-12345"
            }
        }
    }


class PreferenceSuccessResponse(BaseModel):
    """Resposta de sucesso da criação de preferência"""
    success: bool = Field(True, description="Indica sucesso na operação")
    preference_id: str = Field(..., description="ID da preferência")
    init_point: str = Field(..., description="URL do checkout de produção")
    sandbox_init_point: str = Field(..., description="URL do checkout sandbox")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "preference_id": "1234567890-abcdef12-3456-7890",
                "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=1234567890",
                "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=1234567890"
            }
        }
    }


class PaymentInfoResponse(BaseModel):
    """Resposta com informações de um pagamento"""
    success: bool = Field(True, description="Indica sucesso na operação")
    payment: dict = Field(..., description="Dados completos do pagamento")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "payment": {
                    "id": 1234567890,
                    "status": "approved",
                    "status_detail": "accredited",
                    "transaction_amount": 150.00,
                    "currency_id": "BRL",
                    "payment_method_id": "visa",
                    "payment_type_id": "credit_card",
                    "installments": 1,
                    "payer": {
                        "email": "cliente@email.com"
                    },
                    "date_created": "2024-01-15T10:30:00.000-03:00",
                    "date_approved": "2024-01-15T10:30:05.000-03:00"
                }
            }
        }
    }


class WebhookResponse(BaseModel):
    """Resposta do processamento de webhook"""
    status: str = Field(..., description="Status do processamento", examples=["received"])
    message: Optional[str] = Field(None, description="Mensagem adicional")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "received",
                "message": "Webhook processado com sucesso"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Resposta de erro padrão da API"""
    detail: str = Field(..., description="Mensagem de erro")

    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "Não foi possível processar o pagamento. Verifique os dados do cartão."
            }
        }
    }


class HealthResponse(BaseModel):
    """Resposta do health check"""
    status: str = Field(..., description="Status geral da API", examples=["healthy"])
    database: str = Field(..., description="Status da conexão com banco de dados", examples=["healthy"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": "healthy"
            }
        }
    }


class RootResponse(BaseModel):
    """Resposta do endpoint raiz"""
    app: str = Field(..., description="Nome da aplicação")
    version: str = Field(..., description="Versão da API")
    docs: str = Field(..., description="URL da documentação Swagger")

    model_config = {
        "json_schema_extra": {
            "example": {
                "app": "Aprova Fácil API",
                "version": "1.0.0",
                "docs": "/docs"
            }
        }
    }
