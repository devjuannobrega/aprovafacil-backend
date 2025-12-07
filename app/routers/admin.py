from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.user import UserListResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores."
        )
    return current_user


# Users management
@router.get("/users", response_model=List[UserListResponse])
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")

    user.is_active = not user.is_active
    db.commit()

    return {"message": f"Usuario {'ativado' if user.is_active else 'desativado'} com sucesso"}


@router.put("/users/{user_id}/toggle-admin")
def toggle_user_admin(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")

    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Voce nao pode alterar seu proprio status de admin")

    user.is_admin = not user.is_admin
    db.commit()

    return {"message": f"Usuario {'promovido a admin' if user.is_admin else 'rebaixado de admin'} com sucesso"}


# Products management
@router.get("/products", response_model=List[ProductResponse])
def list_all_products(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return products


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_data: ProductCreate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.slug == product_data.slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug ja existe")

    product = Product(
        name=product_data.name,
        slug=product_data.slug,
        description=product_data.description,
        price_pf=product_data.price_pf,
        price_pj=product_data.price_pj
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_data: ProductUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")

    if product_data.name is not None:
        product.name = product_data.name
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.price_pf is not None:
        product.price_pf = product_data.price_pf
    if product_data.price_pj is not None:
        product.price_pj = product_data.price_pj
    if product_data.is_active is not None:
        product.is_active = product_data.is_active

    db.commit()
    db.refresh(product)

    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")

    product.is_active = False
    db.commit()

    return {"message": "Produto desativado com sucesso"}


# Orders management
@router.get("/orders", response_model=List[OrderResponse])
def list_all_orders(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order_detail(order_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado")
    return order


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, status_data: OrderStatusUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido nao encontrado")

    order.status = status_data.status

    if status_data.status == "paid" and not order.paid_at:
        order.paid_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return order


# Dashboard stats
@router.get("/stats")
def get_dashboard_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.status == "paid").count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    total_products = db.query(Product).filter(Product.is_active == True).count()

    from sqlalchemy import func
    total_revenue = db.query(func.sum(Order.total)).filter(Order.status == "paid").scalar() or 0

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,
        "total_products": total_products,
        "total_revenue": float(total_revenue)
    }
