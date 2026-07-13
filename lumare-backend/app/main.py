from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, products, orders, webhooks, shipping, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lumare Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "null",  # covers frontend opened directly as a file:// URL during local dev
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.github\.io|https://.*\.up\.railway\.app|https://.*\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(webhooks.router)
app.include_router(shipping.router)
app.include_router(admin.router)


@app.on_event("startup")
def _seed_on_startup():
    # Populate the initial catalog + admin once. Safe to run on every boot:
    # the seed logic checks for existing rows before inserting, and any failure
    # here is swallowed so it can never prevent the app from starting.
    try:
        from app import seed  # noqa: F401  (import side-effect runs the seed)
    except Exception:
        pass


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "lumare-backend"}
