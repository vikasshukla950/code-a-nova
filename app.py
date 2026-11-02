"""A small, database-backed food delivery app for the Month 3 assignment."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("FOOD_APP_DATABASE", BASE_DIR / "food_delivery.db"))

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "local-food-app-change-me"))

RESTAURANTS = [
    {"id": 1, "name": "Masala Junction", "cuisine": "Indian", "time": "25–35 min", "rating": "4.8", "emoji": "🍛", "color": "saffron"},
    {"id": 2, "name": "Green Garden", "cuisine": "Healthy", "time": "20–30 min", "rating": "4.7", "emoji": "🥗", "color": "green"},
    {"id": 3, "name": "The Noodle House", "cuisine": "Asian", "time": "30–40 min", "rating": "4.6", "emoji": "🍜", "color": "coral"},
    {"id": 4, "name": "Crust & Co.", "cuisine": "Pizza", "time": "25–35 min", "rating": "4.9", "emoji": "🍕", "color": "plum"},
]

MENU = [
    (1, "Paneer Butter Masala", "Creamy tomato curry with fresh paneer", 289, "Veg", "⭐ Bestseller"),
    (1, "Hyderabadi Chicken Biryani", "Slow-cooked basmati rice, chicken and spices", 329, "Non-veg", "Chef's pick"),
    (1, "Dal Tadka & Jeera Rice", "Yellow lentils tempered with garlic and cumin", 219, "Veg", "Comfort food"),
    (2, "Avocado Power Bowl", "Avocado, grains, greens and lemon tahini", 349, "Veg", "Fresh & light"),
    (2, "Crispy Tofu Salad", "Sesame tofu, crunchy vegetables and ginger dressing", 279, "Vegan", "Plant based"),
    (3, "Spicy Miso Ramen", "Rich miso broth, noodles, corn and spring onion", 319, "Veg", "Customer favorite"),
    (3, "Chili Garlic Noodles", "Wok-tossed noodles with vegetables and chili oil", 269, "Veg", "Popular"),
    (4, "Margherita Pizza", "Tomato, mozzarella and fresh basil", 299, "Veg", "Classic"),
    (4, "Smoky Farmhouse Pizza", "Roasted peppers, mushrooms, olives and mozzarella", 389, "Veg", "Bestseller"),
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL CHECK(price >= 0),
            diet TEXT NOT NULL,
            label TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            total INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL
        );
    """)
    if db.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] == 0:
        db.executemany("INSERT INTO menu_items (restaurant_id,name,description,price,diet,label) VALUES (?,?,?,?,?,?)", MENU)
    db.commit()


@app.before_request
def ensure_db() -> None:
    init_db()


def restaurant_by_id(restaurant_id: int) -> dict:
    restaurant = next((r for r in RESTAURANTS if r["id"] == restaurant_id), None)
    if restaurant is None:
        abort(404)
    return restaurant


def cart_details() -> tuple[list[dict], int]:
    cart = session.get("cart", {})
    ids = [int(item_id) for item_id in cart]
    if not ids:
        return [], 0
    rows = get_db().execute(
        f"SELECT * FROM menu_items WHERE id IN ({','.join('?' for _ in ids)})", ids
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["quantity"] = int(cart[str(item["id"])])
        item["subtotal"] = item["price"] * item["quantity"]
        item["restaurant"] = restaurant_by_id(item["restaurant_id"])["name"]
        items.append(item)
    return items, sum(item["subtotal"] for item in items)


@app.context_processor
def inject_cart_count() -> dict:
    return {"cart_count": sum(int(qty) for qty in session.get("cart", {}).values())}


@app.get("/")
def home():
    query = request.args.get("q", "").strip()
    cuisine = request.args.get("cuisine", "").strip()
    restaurants = [r for r in RESTAURANTS if (not cuisine or r["cuisine"] == cuisine)]
    if query:
        restaurants = [r for r in restaurants if query.casefold() in (r["name"] + " " + r["cuisine"]).casefold()]
    return render_template("home.html", restaurants=restaurants, query=query, cuisines=sorted({r["cuisine"] for r in RESTAURANTS}))


@app.get("/restaurants/<int:restaurant_id>")
def restaurant(restaurant_id: int):
    place = restaurant_by_id(restaurant_id)
    items = get_db().execute("SELECT * FROM menu_items WHERE restaurant_id=? ORDER BY id", (restaurant_id,)).fetchall()
    return render_template("restaurant.html", restaurant=place, items=items)


@app.post("/cart/add/<int:item_id>")
def add_to_cart(item_id: int):
    item = get_db().execute("SELECT id FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if item is None:
        abort(404)
    cart = session.get("cart", {})
    cart[str(item_id)] = min(int(cart.get(str(item_id), 0)) + 1, 20)
    session["cart"] = cart
    flash("Added to your bag.", "success")
    return redirect(request.referrer or url_for("home"))


@app.post("/cart/update")
def update_cart():
    cart = session.get("cart", {})
    for item_id in list(cart):
        try:
            quantity = int(request.form.get(item_id, 0))
        except ValueError:
            quantity = 0
        if quantity <= 0:
            cart.pop(item_id, None)
        else:
            cart[item_id] = min(quantity, 20)
    session["cart"] = cart
    flash("Your bag has been updated.", "success")
    return redirect(url_for("view_cart"))


@app.get("/cart")
def view_cart():
    items, total = cart_details()
    return render_template("cart.html", items=items, total=total)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_details()
    if not items:
        flash("Add something delicious before checkout.", "info")
        return redirect(url_for("home"))
    if request.method == "POST":
        customer = request.form.get("customer", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        if not customer or not phone or not address:
            flash("Please fill in your name, phone and delivery address.", "error")
            return render_template("checkout.html", items=items, total=total)
        db = get_db()
        cursor = db.execute("INSERT INTO orders (customer,phone,address,total) VALUES (?,?,?,?)", (customer, phone, address, total))
        order_id = cursor.lastrowid
        db.executemany("INSERT INTO order_items (order_id,item_name,quantity,unit_price) VALUES (?,?,?,?)", [(order_id, item["name"], item["quantity"], item["price"]) for item in items])
        db.commit()
        session["cart"] = {}
        return redirect(url_for("order_confirmation", order_id=order_id))
    return render_template("checkout.html", items=items, total=total)


@app.get("/orders/<int:order_id>")
def order_confirmation(order_id: int):
    order = get_db().execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if order is None:
        abort(404)
    items = get_db().execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    return render_template("order.html", order=order, items=items)


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
