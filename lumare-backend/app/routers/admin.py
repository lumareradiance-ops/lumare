from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, Product, User
from app.schemas import OrderOut, ProductOut
from app.security import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/orders", response_model=list[OrderOut])
def all_orders(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/inventory", response_model=list[ProductOut])
def inventory(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(Product).order_by(Product.stock.asc()).all()


@router.get("/pending-shipments", response_model=list[OrderOut])
def pending_shipments(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return (
        db.query(Order)
        .filter(Order.fulfillment_status.in_(["unfulfilled", "packed"]))
        .order_by(Order.created_at.asc())
        .all()
    )


@router.get("/cod-collections")
def cod_collections(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    cod_orders = (
        db.query(Order)
        .filter(Order.payment_method == "cod", Order.payment_status == "cod_pending")
        .all()
    )
    total_pending = sum(o.total_inr for o in cod_orders)
    return {
        "pending_order_count": len(cod_orders),
        "pending_amount_inr": total_pending,
        "orders": [o.order_number for o in cod_orders],
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.payment_status == "paid").count()
    revenue = (
        db.query(Order)
        .filter(Order.payment_status.in_(["paid"]))
        .with_entities(Order.total_inr)
        .all()
    )
    low_stock = db.query(Product).filter(Product.stock < 10).count()
    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue_inr": sum(r[0] for r in revenue),
        "low_stock_products": low_stock,
    }
