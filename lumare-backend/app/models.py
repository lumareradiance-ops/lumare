import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def gen_id():
        return str(uuid.uuid4())


class Product(Base):
        __tablename__ = "products"

    id = Column(String, primary_key=True, default=gen_id)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    tagline = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    active_ingredient = Column(String, nullable=True)   # e.g. "Niacinamide"
    concentration = Column(String, nullable=True)       # e.g. "10%"
    ph_range = Column(String, nullable=True)
    price_inr = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
        __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Order(Base):
        __tablename__ = "orders"

    id = Column(String, primary_key=True, default=gen_id)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)

    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)

    subtotal_inr = Column(Float, nullable=False)
    shipping_inr = Column(Float, default=0)
    total_inr = Column(Float, nullable=False)

    payment_method = Column(String, default="razorpay")  # razorpay | cod
    payment_status = Column(String, default="pending")    # pending | paid | failed | refunded
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)

    fulfillment_status = Column(String, default="unfulfilled")  # unfulfilled | packed | shipped | delivered | cancelled
    shiprocket_shipment_id = Column(String, nullable=True)
    awb_code = Column(String, nullable=True)
    tracking_url = Column(String, nullable=True)

    odoo_invoice_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
        __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=gen_id)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)

    product_name = Column(String, nullable=False)  # snapshot at time of order
    unit_price_inr = Column(Float, nullable=False)  # snapshot at time of order
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
