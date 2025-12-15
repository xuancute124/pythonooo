import os
from decimal import Decimal
from typing import Dict

from flask import Flask, redirect, render_template, request, session, url_for


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "change-me-in-prod")
    app.config["SESSION_COOKIE_NAME"] = "clothing_shop_session"

    products = [
        {
            "id": "shirt-basic",
            "name": "Áo thun basic",
            "price": Decimal("149000"),
            "thumbnail": "https://via.placeholder.com/300x200?text=Ao+Thun",
        },
        {
            "id": "hoodie",
            "name": "Hoodie nỉ ấm",
            "price": Decimal("329000"),
            "thumbnail": "https://via.placeholder.com/300x200?text=Hoodie",
        },
        {
            "id": "jeans",
            "name": "Quần jean slim",
            "price": Decimal("399000"),
            "thumbnail": "https://via.placeholder.com/300x200?text=Jean",
        },
        {
            "id": "dress",
            "name": "Đầm midi",
            "price": Decimal("459000"),
            "thumbnail": "https://via.placeholder.com/300x200?text=Dress",
        },
    ]
    product_map = {p["id"]: p for p in products}

    def _cart() -> Dict[str, int]:
        return session.setdefault("cart", {})

    def _cart_total(cart: Dict[str, int]) -> Decimal:
        total = Decimal("0")
        for pid, qty in cart.items():
            product = product_map.get(pid)
            if product:
                total += product["price"] * qty
        return total

    @app.route("/")
    def home():
        cart = _cart()
        cart_count = sum(cart.values())
        return render_template(
            "index.html",
            products=products,
            cart_count=cart_count,
        )

    @app.post("/add/<product_id>")
    def add_to_cart(product_id: str):
        qty = max(int(request.form.get("quantity", 1) or 1), 1)
        cart = _cart()
        cart[product_id] = cart.get(product_id, 0) + qty
        session.modified = True
        return redirect(url_for("home"))

    @app.route("/cart")
    def view_cart():
        cart = _cart()
        items = []
        for pid, qty in cart.items():
            product = product_map.get(pid)
            if not product:
                continue
            items.append(
                {
                    "product": product,
                    "quantity": qty,
                    "line_total": product["price"] * qty,
                }
            )
        total = _cart_total(cart)
        return render_template("cart.html", items=items, total=total)

    @app.post("/cart/update")
    def update_cart():
        cart = _cart()
        for pid in list(cart.keys()):
            field = f"quantity_{pid}"
            if field not in request.form:
                continue
            try:
                qty = int(request.form.get(field, 0))
            except ValueError:
                qty = cart.get(pid, 0)
            if qty <= 0:
                cart.pop(pid, None)
            else:
                cart[pid] = qty
        session.modified = True
        return redirect(url_for("view_cart"))

    @app.post("/cart/clear")
    def clear_cart():
        session.pop("cart", None)
        session.modified = True
        return redirect(url_for("home"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

