import xmlrpc.client

from app.config import settings

_uid_cache = {"uid": None}


def _common_proxy():
    return xmlrpc.client.ServerProxy(f"{settings.odoo_url}/xmlrpc/2/common")


def _models_proxy():
    return xmlrpc.client.ServerProxy(f"{settings.odoo_url}/xmlrpc/2/object")


def _authenticate() -> int:
    """Authenticates once per process and caches the resulting uid."""
    if _uid_cache["uid"] is not None:
        return _uid_cache["uid"]

    if not all([settings.odoo_url, settings.odoo_db, settings.odoo_username, settings.odoo_api_key]):
        raise RuntimeError(
            "Odoo credentials are not set. Add ODOO_URL, ODOO_DB, ODOO_USERNAME, "
            "and ODOO_API_KEY to your .env"
        )

    uid = _common_proxy().authenticate(
        settings.odoo_db, settings.odoo_username, settings.odoo_api_key, {}
    )
    if not uid:
        raise RuntimeError("Odoo authentication failed — check ODOO_DB/ODOO_USERNAME/ODOO_API_KEY")

    _uid_cache["uid"] = uid
    return uid


def _execute(model: str, method: str, *args):
    uid = _authenticate()
    return _models_proxy().execute_kw(
        settings.odoo_db, uid, settings.odoo_api_key, model, method, list(args)
    )


def _find_or_create_partner(name: str, email: str) -> int:
    """Odoo invoices are attached to a res.partner (contact) record."""
    existing = _execute("res.partner", "search", [[["email", "=", email]]])
    if existing:
        return existing[0]

    return _execute("res.partner", "create", [{
        "name": name,
        "email": email,
    }])


def create_invoice(order, items) -> dict:
    """
    Creates and posts a customer invoice (account.move) in Odoo for a paid order.
    GST/tax computation follows whatever fiscal position and taxes are configured
    on the product/partner in your Odoo instance — configure those in the Odoo UI first.
    """
    partner_id = _find_or_create_partner(order.customer_name, order.customer_email)

    invoice_id = _execute("account.move", "create", [{
        "move_type": "out_invoice",
        "partner_id": partner_id,
        "invoice_origin": order.order_number,
        "invoice_line_ids": [
            (0, 0, {
                "name": item.product_name,
                "quantity": item.quantity,
                "price_unit": item.unit_price_inr,
            })
            for item in items
        ],
    }])

    # Posting finalizes the invoice (assigns a real invoice number, locks it for editing).
    _execute("account.move", "action_post", [[invoice_id]])

    invoice = _execute("account.move", "read", [[invoice_id]], {"fields": ["name", "id"]})
    return {"invoice_id": invoice_id, "invoice_number": invoice[0]["name"]}
