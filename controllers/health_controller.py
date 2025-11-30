from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.database import get_db
from core.config import settings
from schemas.payment import RootResponse, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Informações da API",
    description="""
Endpoint raiz que retorna informações básicas sobre a API.

**Retorna:**
- Nome da aplicação
- Versão atual
- Link para a documentação Swagger

**Uso típico:**
Útil para verificar se a API está online e qual versão está em execução.
    """,
    responses={
        200: {
            "description": "Informações da API",
            "content": {
                "application/json": {
                    "example": {
                        "app": "Aprova Fácil API",
                        "version": "1.0.0",
                        "docs": "/docs"
                    }
                }
            }
        }
    }
)
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""
Verifica o status de saúde da API e suas dependências.

**Verificações realizadas:**
- Conexão com o banco de dados PostgreSQL

**Status possíveis:**
- `healthy`: Todos os serviços funcionando normalmente
- `degraded`: Algum serviço com problemas (API ainda funcional)
- `unhealthy`: Serviços críticos indisponíveis

**Uso típico:**
- Monitoramento de infraestrutura
- Load balancers para verificar disponibilidade
- Kubernetes liveness/readiness probes
    """,
    responses={
        200: {
            "description": "Status de saúde da API",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Todos os serviços saudáveis",
                            "value": {
                                "status": "healthy",
                                "database": "healthy"
                            }
                        },
                        "degraded": {
                            "summary": "Banco de dados com problemas",
                            "value": {
                                "status": "degraded",
                                "database": "unhealthy: Connection refused"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
    }
