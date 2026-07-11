from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, User
from app.schemas import ProductOut, ProductCreate
from app.security import require_admin

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
      return db.query(Product).filter(Product.is_active == True).all()  # noqa: E712


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
      product = db.query(Product).filter(Product.id == product_id).first()
      if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return product


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
      payload: ProductCreate,
      db: Session = Depends(get_db),
      _admin: User = Depends(require_admin),
):
      existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
              raise HTTPException(status_code=409, detail="A product with this SKU already exists")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}/stock", response_model=ProductOut)
def adjust_stock(
      product_id: str,
      delta: int,
      db: Session = Depends(get_db),
      _admin: User = Depends(require_admin),
):
      product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
              raise HTTPException(status_code=404, detail="Product not found")
          product.stock = max(0, product.stock + delta)
    db.commit()
    db.refresh(product)
    return product
