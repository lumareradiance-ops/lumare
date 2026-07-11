import random
import string

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Order, OrderItem, Product, User
from app.schemas import CreateOrderRequest, OrderOut, RazorpayVerifyRequest
from app.security import get_current_user_optional
from app.services import razorpay_service, shiprocket_service, odoo_service

router = APIRouter(prefix="/api/orders", tags=["orders"])

FREE_SHIPPING_THRESHOLD = 599
FLAT_SHIPPING_INR = 79


def generate_order_number() -> str:
      suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
      return f"LMR-{suffix}"


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
      payload: CreateOrderRequest,
      db: Session = Depends(get_db),
      user: User | None = Depends(get_current_user_optional),
):
      if not payload.items:
                raise HTTPException(status_code=400, detail="Cart is empty")

      subtotal = 0.0
      order_items = []

    # Prices and stock are always read from the database, never trusted from the client.
      for line in payload.items:
                product = db.query(Product).filter(Product.id == line.product_id).first()
                if not product or not product.is_active:
                              raise HTTPException(status_code=404, detail=f"Product {line.product_id} not found")
                          if product.stock < line.quantity:
                                        raise HTTPException(status_code=409, detail=f"'{product.name}' is out of stock")
                                    subtotal += product.price_inr * line.quantity
                order_items.append((product, line.quantity))

      shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else FLAT_SHIPPING_INR
      total = subtotal + shipping

    order = Order(
              order_number=generate_order_number(),
              user_id=user.id if user else None,
              customer_name=payload.address.customer_name,
              customer_email=payload.address.customer_email,
              customer_phone=payload.address.customer_phone,
              address_line1=payload.address.address_line1,
              address_line2=payload.address.address_line2,
              city=payload.address.city,
              state=payload.address.state,
              pincode=payload.address.pincode,
              subtotal_inr=subtotal,
              shipping_inr=shipping,
              total_inr=total,
              payment_method=payload.payment_method,
              payment_status="pending" if payload.payment_method == "razorpay" else "cod_pending",
    )
    db.add(order)
    db.flush()  # get order.id before adding items

    for product, qty in order_items:
              db.add(OrderItem(
                            order_id=order.id,
                            product_id=product.id,
                            product_name=product.name,
                            unit_price_inr=product.price_inr,
                            quantity=qty,
              ))
              product.stock -= qty  # reserve stock immediately

    db.commit()
    db.refresh(order)

    if payload.payment_method == "razorpay":
              try:
                            rp_order = razorpay_service.create_razorpay_order(total, receipt=order.order_number)
                            order.razorpay_order_id = rp_order["id"]
                            db.commit()
                            db.refresh(order)
except RuntimeError as e:
            # Razorpay isn't configured yet — order still exists, just can't be paid for online yet.
            raise HTTPException(status_code=503, detail=str(e))
else:
        # COD orders can be handed to Shiprocket right away.
          _try_create_shipment(db, order)

    return order


@router.post("/verify-payment", response_model=OrderOut)
def verify_payment(payload: RazorpayVerifyRequest, db: Session = Depends(get_db)):
      order = db.query(Order).filter(Order.id == payload.order_id).first()
      if not order:
                raise HTTPException(status_code=404, detail="Order not found")

      valid = razorpay_service.verify_payment_signature(
          payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature
      )
      if not valid:
                order.payment_status = "failed"
                db.commit()
                raise HTTPException(status_code=400, detail="Payment verification failed")

      order.payment_status = "paid"
      order.razorpay_payment_id = payload.razorpay_payment_id
      db.commit()
      db.refresh(order)

    _try_create_shipment(db, order)
    _try_create_invoice(db, order)

    return order


def _try_create_shipment(db: Session, order: Order):
      try:
                result = shiprocket_service.create_shipment(order, order.items)
                order.shiprocket_shipment_id = str(result.get("shipment_id", ""))
                order.fulfillment_status = "packed"
                db.commit()
except Exception:
        # Shipping isn't configured yet, or Shiprocket rejected the payload.
        # The order still exists and can be retried manually from the admin dashboard.
        pass


def _try_create_invoice(db: Session, order: Order):
      try:
                result = odoo_service.create_invoice(order, order.items)
                order.odoo_invoice_id = str(result.get("invoice_number", ""))
                db.commit()
except Exception:
        # Odoo isn't configured yet — invoice can be generated manually later.
        pass


@router.get("/track/{order_number}", response_model=OrderOut)
def track_order(order_number: str, db: Session = Depends(get_db)):
      order = db.query(Order).filter(Order.order_number == order_number).first()
      if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            return order


@router.get("/mine", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user_optional)):
      if not user:
                raise HTTPException(status_code=401, detail="Login required to view order history")
            return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
