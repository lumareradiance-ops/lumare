# Lumare Backend

FastAPI + PostgreSQL backend for products, auth, orders, Razorpay payments, Shiprocket shipping, and Zoho Books invoicing. Includes a lightweight admin dashboard (admin/index.html).

## Run it locally

Commands: cd lumare-backend, then python -m venv venv, then source venv/bin/activate, then pip install -r requirements.txt, then cp .env.example .env, then python -m app.seed, then uvicorn app.main:app --reload --port 8000

Health check: GET http://localhost:8000/api/health
Interactive API docs: http://localhost:8000/docs

Open admin/index.html in a browser, log in with the seeded admin account, then change that password immediately.

## Deploying to Railway

Create a new Railway project and add a PostgreSQL plugin. Add a service from this repo with start command uvicorn app.main:app --host 0.0.0.0 --port dollar-PORT. Copy every variable from .env.example into the service Variables tab with real values. Run python -m app.seed once via Railway's Shell feature.

## Third-party accounts needed

Razorpay: sign up at razorpay.com, complete KYC, generate API keys in Settings, add a webhook for payment.captured and payment.failed.

Shiprocket: sign up at shiprocket.in, add a pickup address, put the login email and password in .env.

Zoho Books: set up an organization, create a Self Client at api-console.zoho.com, generate a refresh token, put client id, secret, refresh token, and org id in .env.

## API reference

POST /api/auth/register and /login. GET /api/products and /products/id. POST /api/orders for checkout. POST /api/orders/verify-payment. GET /api/orders/track/order_number. GET /api/orders/mine. POST /api/webhooks/razorpay. POST /api/shipping/refresh/order_number. GET /api/admin/orders, /admin/inventory, /admin/pending-shipments, /admin/cod-collections, /admin/summary.

## Notes

Razorpay integration is fully wired and tested against their documented API shape. Shiprocket integration is wired but package dimensions are placeholders. Zoho Books integration is wired but GST behavior depends on your organization's tax configuration. Stock is reserved at checkout time, not at payment confirmation.
