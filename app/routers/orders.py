from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person_type = order_data.person_type or current_user.person_type or "pf"

    order = Order(
        user_id=current_user.id,
        status="pending",
        person_type=person_type,
        subtotal=Decimal("0"),
        total=Decimal("0"),
        notes=order_data.notes
    )
    db.add(order)
    db.flush()

    subtotal = Decimal("0")

    for item_data in order_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id, Product.is_active == True).first()
        if not product:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produto {item_data.product_id} nao encontrado"
            )

        unit_price = product.price_pj if person_type == "pj" else product.price_pf
        total_price = unit_price * item_data.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            quantity=item_data.quantity,
            unit_price=unit_price,
            total_price=total_price
        )
        db.add(order_item)
        subtotal += total_price

    order.subtotal = subtotal
    order.total = subtotal

    db.commit()
    db.refresh(order)

    return order


@router.get("", response_model=List[OrderResponse])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
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
    return order
