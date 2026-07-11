"""
Run once after the database is up: python -m app.seed
Creates the initial product catalog and one admin user (change the password after first login).
"""
from app.database import SessionLocal, Base, engine
from app.models import Product, User
from app.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

products = [
      dict(sku="BRIGHT-10", name="Brightening Serum", tagline="Visibly brightens · 30ml",
                    description="10% Niacinamide, Alpha Arbutin, and Licorice Extract — visibly brightens, evens tone, and boosts natural glow.",
                    active_ingredient="Niacinamide", concentration="10%", ph_range="5.0-5.8",
                    price_inr=799, stock=100),
      dict(sku="MULTI-ACT", name="Multi-Active Serum", tagline="Hydrate. Balance. Strengthen. · 30ml",
                    description="10% Micro Ferment Extracts, Hydrating Complex, Pre + Probiotics — for dewy, healthy-looking skin.",
                    active_ingredient="Micro Ferment Extracts", concentration="10%", ph_range="5.5-6.5",
                    price_inr=849, stock=90),
      dict(sku="HYDRA-GEL", name="Hydrated Gel", tagline="Deep hydration · 50g",
                    description="Ceramides, Hyaluronic Acid, and Squalane — deep hydration that strengthens the barrier for lasting comfort.",
                    active_ingredient="Hyaluronic Acid", concentration="—", ph_range="5.5-6.5",
                    price_inr=749, stock=110),
]

for p in products:
      if not db.query(Product).filter(Product.sku == p["sku"]).first():
                db.add(Product(**p))

  admin_email = "admin@lumare.in"
if not db.query(User).filter(User.email == admin_email).first():
      db.add(User(
                name="Lumare Admin",
                email=admin_email,
                password_hash=hash_password("change-this-password"),
                is_admin=True,
      ))

db.commit()
db.close()
print("Seed complete. Admin login: admin@lumare.in / change-this-password (change this immediately)")
