from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------
class RegisterRequest(BaseModel):
      name: str
      email: EmailStr
      password: str
      phone: Optional[str] = None


class LoginRequest(BaseModel):
      email: EmailStr
      password: str


class UserOut(BaseModel):
      id: str
      name: str
      email: str
      is_admin: bool

    class Config:
              from_attributes = True


class TokenResponse(BaseModel):
      token: str
      user: UserOut


# ---------- Products ----------
class ProductOut(BaseModel):
      id: str
      sku: str
      name: str
      tagline: Optional[str] = None
      description: Optional[str] = None
      active_ingredient: Optional[str] = None
      concentration: Optional[str] = None
      ph_range: Optional[str] = None
      price_inr: float
      stock: int
      is_active: bool

    class Config:
              from_attributes = True


class ProductCreate(BaseModel):
      sku: str
      name: str
      tagline: Optional[str] = None
      description: Optional[str] = None
      active_ingredient: Optional[str] = None
      concentration: Optional[str] = None
      ph_range: Optional[str] = None
      price_inr: float
      stock: int = 0


# ---------- Orders ----------
class OrderItemIn(BaseModel):
      product_id: str
      quantity: int


class ShippingAddress(BaseModel):
      customer_name: str
      customer_email: EmailStr
      customer_phone: str
      address_line1: str
      address_line2: Optional[str] = None
      city: str
      state: str
      pincode: str


class CreateOrderRequest(BaseModel):
      items: List[OrderItemIn]
      address: ShippingAddress
      payment_method: str = "razorpay"  # "razorpay" or "cod"


class OrderItemOut(BaseModel):
      product_name: str
      unit_price_inr: float
      quantity: int

    class Config:
              from_attributes = True


class OrderOut(BaseModel):
      id: str
      order_number: str
      customer_name: str
      customer_email: str
      subtotal_inr: float
      shipping_inr: float
      total_inr: float
      payment_method: str
      payment_status: str
      fulfillment_status: str
      razorpay_order_id: Optional[str] = None
      awb_code: Optional[str] = None
      tracking_url: Optional[str] = None
      created_at: datetime
      items: List[OrderItemOut]

    class Config:
              from_attributes = True


class RazorpayVerifyRequest(BaseModel):
      order_id: str  # our internal order id
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
