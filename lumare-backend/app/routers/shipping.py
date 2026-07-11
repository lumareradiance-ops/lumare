from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, User
from app.security import require_admin
from app.services import shiprocket_service

router = APIRouter(prefix="/api/shipping", tags=["shipping"])


@router.post("/refresh/{order_number}")
def refresh_tracking(
      order_number: str,
      db: Session = Depends(get_db),
      _admin: User = Depends(require_admin),
):
      order = db.query(Order).filter(Order.order_number == order_number).first()
      if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            if not order.awb_code:
                      raise HTTPException(status_code=400, detail="No AWB assigned to this order yet")

    tracking = shiprocket_service.track_shipment(order.awb_code)
    if tracking is None:
              raise HTTPException(status_code=502, detail="Could not reach Shiprocket")

    current_status = tracking.get("tracking_data", {}).get("shipment_status")
    if current_status:
              order.fulfillment_status = current_status
              db.commit()

    return tracking
