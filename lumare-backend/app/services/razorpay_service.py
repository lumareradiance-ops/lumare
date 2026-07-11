import hashlib
import hmac

import razorpay

from app.config import settings


def get_client() -> razorpay.Client:
      if not settings.razorpay_key_id or not settings.razorpay_key_secret:
                raise RuntimeError(
                              "Razorpay keys are not set. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to your .env"
                )
            client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return client


def create_razorpay_order(amount_inr: float, receipt: str) -> dict:
      """Amount must be in paise (INR * 100) per Razorpay's API."""
    client = get_client()
    return client.order.create({
              "amount": int(round(amount_inr * 100)),
              "currency": "INR",
              "receipt": receipt,
              "payment_capture": 1,
    })


def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
      """Called after checkout completes on the frontend, before marking the order paid."""
    client = get_client()
    try:
              client.utility.verify_payment_signature({
                            "razorpay_order_id": razorpay_order_id,
                            "razorpay_payment_id": razorpay_payment_id,
                            "razorpay_signature": razorpay_signature,
              })
              return True
except razorpay.errors.SignatureVerificationError:
        return False


def verify_webhook_signature(payload_body: bytes, received_signature: str) -> bool:
      """Called on the /webhooks/razorpay endpoint Razorpay posts to directly."""
    if not settings.razorpay_webhook_secret:
              raise RuntimeError("RAZORPAY_WEBHOOK_SECRET is not set")
          expected_signature = hmac.new(
                    key=settings.razorpay_webhook_secret.encode(),
                    msg=payload_body,
                    digestmod=hashlib.sha256,
          ).hexdigest()
    return hmac.compare_digest(expected_signature, received_signature)
