from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db
from controllers import payment_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


DESCRIPTION = """
## Aprova Fácil API

API backend para integração com **Mercado Pago Bricks** - a solução de pagamentos do Mercado Pago.

### Funcionalidades

* **Processar pagamentos** com cartão de crédito/débito via Card Payment Brick
* **Criar preferências** para Checkout Pro e Payment Brick
* **Consultar parcelamento** em tempo real baseado no BIN do cartão
* **Webhooks** para receber notificações de pagamentos

### Autenticação

A maioria dos endpoints requer autenticação via **API Key** no header:

```
X-API-Key: sua-api-key-aqui
```

Clique no botão **Authorize** acima e insira sua API Key para testar os endpoints.

O endpoint de webhook (`POST /api/payment/webhook`) **não requer autenticação** pois é chamado diretamente pelo Mercado Pago.

### Ambiente de Testes

Para testes, utilize as [credenciais de sandbox do Mercado Pago](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/credentials).

### Links Úteis

* [Documentação Mercado Pago Bricks](https://www.mercadopago.com.br/developers/pt/docs/checkout-bricks/landing)
* [Cartões de teste](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/test/cards)
"""

app = FastAPI(
    title=settings.APP_NAME,
    description=DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    contact={
        "name": "Suporte Aprova Fácil",
        "email": "suporte@aprovafacil.com.br",
    },
    license_info={
        "name": "Proprietário",
    },
    openapi_tags=[
        {
            "name": "Health",
            "description": "Endpoints de monitoramento e status da API",
        },
        {
            "name": "Payment",
            "description": "Endpoints para processamento de pagamentos via Mercado Pago",
        },
        {
            "name": "Webhook",
            "description": "Endpoint para receber notificações do Mercado Pago",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(payment_router)
