from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order
from app.services import razorpay_service
from app.routers.orders import _try_create_shipment, _try_create_invoice

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not razorpay_service.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.captured":
        rp_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        rp_payment_id = payload["payload"]["payment"]["entity"]["id"]

        order = db.query(Order).filter(Order.razorpay_order_id == rp_order_id).first()
        if order and order.payment_status != "paid":
            order.payment_status = "paid"
            order.razorpay_payment_id = rp_payment_id
            db.commit()
            _try_create_shipment(db, order)
            _try_create_invoice(db, order)

    elif event == "payment.failed":
        rp_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        order = db.query(Order).filter(Order.razorpay_order_id == rp_order_id).first()
        if order:
            order.payment_status = "failed"
            db.commit()

    return {"status": "ok"}
