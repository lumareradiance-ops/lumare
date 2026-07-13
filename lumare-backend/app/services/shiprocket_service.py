import time
from typing import Optional

import httpx

from app.config import settings

SHIPROCKET_BASE = "https://apiv2.shiprocket.in/v1/external"

_token_cache = {"token": None, "expires_at": 0}


def get_auth_token() -> str:
    """Shiprocket tokens are valid ~10 days; cached in memory per process."""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    if not settings.shiprocket_email or not settings.shiprocket_password:
        raise RuntimeError(
            "Shiprocket credentials are not set. Add SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD to your .env"
        )

    resp = httpx.post(
        f"{SHIPROCKET_BASE}/auth/login",
        json={"email": settings.shiprocket_email, "password": settings.shiprocket_password},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["token"]
    _token_cache["expires_at"] = now + 9 * 24 * 3600  # refresh a day early
    return data["token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_auth_token()}"}


def create_shipment(order, items) -> dict:
    """
    Creates a Shiprocket order + shipment from our internal Order + OrderItem rows.
    Returns the raw Shiprocket response, which includes shipment_id and (once assigned) awb_code.
    """
    payload = {
        "order_id": order.order_number,
        "order_date": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "pickup_location": settings.shiprocket_pickup_location,
        "billing_customer_name": order.customer_name,
        "billing_last_name": "",
        "billing_address": order.address_line1,
        "billing_address_2": order.address_line2 or "",
        "billing_city": order.city,
        "billing_pincode": order.pincode,
        "billing_state": order.state,
        "billing_country": "India",
        "billing_email": order.customer_email,
        "billing_phone": order.customer_phone,
        "shipping_is_billing": True,
        "order_items": [
            {
                "name": item.product_name,
                "sku": item.product_id,
                "units": item.quantity,
                "selling_price": item.unit_price_inr,
            }
            for item in items
        ],
        "payment_method": "Prepaid" if order.payment_method == "razorpay" else "COD",
        "sub_total": order.subtotal_inr,
        # Package dimensions are placeholders — set real values for your packaging.
        "length": 10,
        "breadth": 10,
        "height": 10,
        "weight": 0.3,
    }
    resp = httpx.post(
        f"{SHIPROCKET_BASE}/orders/create/adhoc",
        json=payload,
        headers=_headers(),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def track_shipment(awb_code: str) -> Optional[dict]:
    resp = httpx.get(
        f"{SHIPROCKET_BASE}/courier/track/awb/{awb_code}",
        headers=_headers(),
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    return resp.json()
