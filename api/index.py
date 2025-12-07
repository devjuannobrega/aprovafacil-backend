import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth_router, products_router, orders_router, payment_router, admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aprova Facil API",
    description="API para sistema de recuperacao de credito",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://aprovafacil-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(payment_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "Aprova Facil API", "version": "1.0.0"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
