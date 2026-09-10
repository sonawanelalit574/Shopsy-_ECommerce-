

import sqlite3
import os
import urllib.parse
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# ----------------------------------------------------------------------
# APP CONFIG
# ----------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "shopsy-dev-secret-key-change-this-in-production"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shopsy.db")


# ----------------------------------------------------------------------
# DATABASE HELPERS
# ----------------------------------------------------------------------
def get_db():
    """Open (or reuse) a SQLite connection for this request."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def img(name, bg):
    """Build a clean placeholder product image (swap for real photos anytime)."""
    text = urllib.parse.quote(name)
    return f"https://placehold.co/500x400/{bg}/ffffff?font=roboto&text={text}"


CATEGORY_COLORS = {
    "Grocery": "1f7a4d",
    "Fruits & Vegetables": "3fa34d",
    "Mobiles": "2b3a67",
    "Electronics": "35507a",
    "Fashion": "a6436b",
    "Home & Kitchen": "b5651d",
    "Beauty": "8e44ad",
    "Books": "6b4f3f",
}

# Categories that qualify for Shopsy's "Quick Delivery" (15-minute) promise —
# just like the real quick-commerce apps (Blinkit / Zepto style).
QUICK_DELIVERY_CATEGORIES = {"Grocery", "Fruits & Vegetables"}

PRODUCTS = [
    # name, category, price, unit, stock, description
    ("Fresh Toned Milk 1L", "Grocery", 62, "1 L pack", 120, "Farm-fresh toned milk, pasteurized daily."),
    ("Brown Bread 400g", "Grocery", 45, "1 pack", 80, "Soft whole-wheat brown bread, baked fresh."),
    ("Farm Eggs (12 pcs)", "Grocery", 84, "1 tray", 60, "Protein-rich country eggs, tray of 12."),
    ("India Gate Basmati Rice 5kg", "Grocery", 549, "5 kg bag", 40, "Long-grain aged basmati rice, aromatic and fluffy."),
    ("Tata Sugar 1kg", "Grocery", 48, "1 kg pack", 100, "Refined, hygienically packed sugar."),
    ("Fortune Sunflower Oil 1L", "Grocery", 149, "1 L bottle", 70, "Light, healthy cooking oil, rich in Vitamin E."),
    ("Amul Butter 500g", "Grocery", 265, "500 g pack", 55, "Creamy, delicious butter — a household favourite."),
    ("Red Label Tea 500g", "Grocery", 210, "500 g pack", 65, "Strong, flavourful blended tea leaves."),
    ("Fresh Apples (Shimla) 1kg", "Fruits & Vegetables", 159, "1 kg", 90, "Crisp, juicy Shimla apples, hand-picked."),
    ("Robusta Bananas (1 dozen)", "Fruits & Vegetables", 49, "12 pcs", 90, "Naturally ripened, sweet bananas."),
    ("Fresh Tomatoes 1kg", "Fruits & Vegetables", 39, "1 kg", 100, "Farm-fresh, firm red tomatoes."),
    ("Onions 1kg", "Fruits & Vegetables", 34, "1 kg", 100, "Premium quality onions, straight from the farm."),
    ("Potatoes 1kg", "Fruits & Vegetables", 29, "1 kg", 100, "Fresh potatoes, perfect for everyday cooking."),
    ("Green Capsicum 500g", "Fruits & Vegetables", 35, "500 g", 60, "Crunchy, fresh green capsicum."),
    ("Samsung Galaxy M14 5G", "Mobiles", 11499, "1 unit", 25, "6.6-inch display, 6000mAh battery, 50MP camera."),
    ("Redmi Note 13", "Mobiles", 16999, "1 unit", 20, "AMOLED display, 108MP camera, fast charging."),
    ("Apple iPhone 13", "Mobiles", 54900, "1 unit", 10, "A15 Bionic chip, dual camera system, iOS."),
    ("boAt Airdopes 141 Earbuds", "Electronics", 1299, "1 pair", 45, "42H playback, ENx tech, IPX4 water resistance."),
    ("HP 15s Laptop (i5, 8GB)", "Electronics", 46990, "1 unit", 12, "11th Gen i5, 8GB RAM, 512GB SSD, Windows 11."),
    ("Mi Power Bank 3i 20000mAh", "Electronics", 1699, "1 unit", 35, "Dual output, 18W fast charging, triple layer protection."),
    ("Men's Cotton T-Shirt", "Fashion", 399, "1 pc", 150, "Breathable, comfortable regular-fit cotton tee."),
    ("Women's Printed Kurti", "Fashion", 599, "1 pc", 100, "Rayon fabric, three-quarter sleeves, casual wear."),
    ("Running Sports Shoes", "Fashion", 1299, "1 pair", 70, "Lightweight, cushioned sole, breathable mesh upper."),
    ("Non-Stick Frying Pan 26cm", "Home & Kitchen", 649, "1 pc", 40, "Durable non-stick coating, induction friendly."),
    ("LED Bulb 9W (Pack of 4)", "Home & Kitchen", 349, "4 pcs", 90, "Cool white light, energy saving, long lasting."),
    ("Cotton Bedsheet Set (King)", "Home & Kitchen", 899, "1 set", 50, "Soft cotton bedsheet with 2 pillow covers."),
    ("Herbal Face Wash 150ml", "Beauty", 199, "150 ml", 80, "Gentle, soap-free formula for daily use."),
    ("Anti-Hairfall Shampoo 340ml", "Beauty", 249, "340 ml", 75, "Strengthens roots, reduces hair fall from breakage."),
    ("Matte Lipstick", "Beauty", 349, "1 pc", 60, "Long-lasting, richly pigmented matte finish."),
    ("Bestselling Fiction Novel", "Books", 299, "1 pc", 40, "A gripping page-turner loved by readers everywhere."),
    ("A5 Notebook (Set of 3)", "Books", 189, "3 pcs", 100, "Ruled pages, durable binding, ideal for school or office."),
]


def init_db():
    """Create tables and seed sample products if the DB is empty."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            address TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT,
            stock INTEGER DEFAULT 50,
            description TEXT,
            image TEXT,
            quick_delivery INTEGER DEFAULT 0,
            rating REAL DEFAULT 4.2
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            delivery_type TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Placed'
        );
        """
    )
    db.commit()

    count = db.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count == 0:
        for name, category, price, unit, stock, desc in PRODUCTS:
            bg = CATEGORY_COLORS.get(category, "444444")
            quick = 1 if category in QUICK_DELIVERY_CATEGORIES else 0
            db.execute(
                """INSERT INTO products
                   (name, category, price, unit, stock, description, image, quick_delivery, rating)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, category, price, unit, stock, desc, img(name, bg), quick, 4.0 + (hash(name) % 10) / 10),
            )
        db.commit()
    db.close()


# ----------------------------------------------------------------------
# AUTH HELPERS
# ----------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    if session.get("user_id"):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    return None


@app.context_processor
def inject_globals():
    """Make cart count and the logged-in user available in every template."""
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return {
        "cart_count": cart_count,
        "current_user": current_user(),
        "categories": list(CATEGORY_COLORS.keys()),
    }


# ----------------------------------------------------------------------
# CART HELPERS  (cart lives in the session as {product_id_str: qty})
# ----------------------------------------------------------------------
def get_cart_details():
    db = get_db()
    cart = session.get("cart", {})
    items = []
    total = 0
    has_quick_item = False
    for pid, qty in cart.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if not product:
            continue
        subtotal = product["price"] * qty
        total += subtotal
        if product["quick_delivery"]:
            has_quick_item = True
        items.append({"product": product, "qty": qty, "subtotal": subtotal})
    return items, total, has_quick_item


# ----------------------------------------------------------------------
# ROUTES — BROWSE
# ----------------------------------------------------------------------
@app.route("/")
def home():
    db = get_db()
    query = request.args.get("q", "").strip()
    if query:
        like = f"%{query}%"
        products = db.execute(
            "SELECT * FROM products WHERE name LIKE ? OR category LIKE ?", (like, like)
        ).fetchall()
        return render_template("index.html", products=products, search=query, is_search=True)

    quick_products = db.execute(
        "SELECT * FROM products WHERE quick_delivery = 1 ORDER BY RANDOM() LIMIT 8"
    ).fetchall()
    featured = db.execute(
        "SELECT * FROM products WHERE quick_delivery = 0 ORDER BY RANDOM() LIMIT 8"
    ).fetchall()
    return render_template(
        "index.html", quick_products=quick_products, featured=featured, is_search=False
    )


@app.route("/category/<name>")
def category(name):
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE category = ?", (name,)).fetchall()
    return render_template("category.html", products=products, category_name=name)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("home"))
    related = db.execute(
        "SELECT * FROM products WHERE category = ? AND id != ? LIMIT 4",
        (product["category"], product_id),
    ).fetchall()
    return render_template("product.html", product=product, related=related)


# ----------------------------------------------------------------------
# ROUTES — CART
# ----------------------------------------------------------------------
@app.route("/cart")
def cart_page():
    items, total, has_quick_item = get_cart_details()
    delivery_fee = 0 if total >= 499 or total == 0 else 25
    return render_template(
        "cart.html", items=items, total=total, delivery_fee=delivery_fee,
        has_quick_item=has_quick_item, grand_total=total + delivery_fee,
    )


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        return jsonify({"ok": False, "message": "Product not found."}), 404

    cart = session.get("cart", {})
    key = str(product_id)
    qty = int(request.form.get("qty", 1))
    cart[key] = cart.get(key, 0) + qty
    session["cart"] = cart
    session.modified = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "cart_count": sum(cart.values())})
    flash(f"Added {product['name']} to your cart.", "success")
    return redirect(request.referrer or url_for("home"))


@app.route("/cart/update/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    cart = session.get("cart", {})
    key = str(product_id)
    action = request.form.get("action")
    if key in cart:
        if action == "increase":
            cart[key] += 1
        elif action == "decrease":
            cart[key] -= 1
            if cart[key] <= 0:
                del cart[key]
        elif action == "remove":
            del cart[key]
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart_page"))


@app.route("/cart/clear")
def clear_cart():
    session["cart"] = {}
    return redirect(url_for("cart_page"))


# ----------------------------------------------------------------------
# ROUTES — AUTH
# ----------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        phone = request.form.get("phone", "").strip()

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with this email already exists. Please log in.", "error")
            return redirect(url_for("login"))

        db.execute(
            "INSERT INTO users (name, email, password_hash, phone) VALUES (?, ?, ?, ?)",
            (name, email, generate_password_hash(password), phone),
        )
        db.commit()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        session["user_id"] = user["id"]
        flash(f"Welcome to Shopsy, {name}!", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ----------------------------------------------------------------------
# ROUTES — CHECKOUT & SMART PAYMENTS
# ----------------------------------------------------------------------
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, total, has_quick_item = get_cart_details()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("home"))

    delivery_fee = 0 if total >= 499 else 25
    grand_total = total + delivery_fee
    user = current_user()

    if request.method == "POST":
        address = request.form.get("address", "").strip()
        payment_method = request.form.get("payment_method")
        if not address:
            flash("Please enter a delivery address.", "error")
            return redirect(url_for("checkout"))

        # --- Smart payment handling -------------------------------------
        # cod            -> Cash on Delivery, confirmed immediately
        # upi / card     -> simulated instant "online payment" gateway
        if payment_method == "cod":
            payment_status = "Pending (Pay on Delivery)"
        elif payment_method in ("upi", "card"):
            # In production, integrate Razorpay / Stripe / Paytm here and
            # verify the real transaction before marking this "Paid".
            payment_status = "Paid"
        else:
            flash("Please choose a valid payment method.", "error")
            return redirect(url_for("checkout"))

        delivery_type = "Quick Delivery (15 min)" if has_quick_item and len(items) == sum(
            1 for i in items if i["product"]["quick_delivery"]
        ) else ("Mixed Delivery" if has_quick_item else "Standard Delivery (2-5 days)")

        import json
        items_snapshot = [
            {"name": i["product"]["name"], "qty": i["qty"], "price": i["product"]["price"]}
            for i in items
        ]
        db = get_db()
        db.execute(
            """INSERT INTO orders
               (user_id, items_json, total, payment_method, payment_status, delivery_type, address, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user["id"], json.dumps(items_snapshot), grand_total, payment_method,
                payment_status, delivery_type, address, datetime.now().strftime("%d %b %Y, %I:%M %p"),
            ),
        )
        db.commit()
        order_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        session["cart"] = {}
        eta = (datetime.now() + timedelta(minutes=15)) if has_quick_item else (datetime.now() + timedelta(days=3))
        return render_template(
            "order_success.html", order_id=order_id, payment_method=payment_method,
            payment_status=payment_status, delivery_type=delivery_type,
            grand_total=grand_total, eta=eta,
        )

    return render_template(
        "checkout.html", items=items, total=total, delivery_fee=delivery_fee,
        grand_total=grand_total, has_quick_item=has_quick_item, user=user,
    )


@app.route("/orders")
@login_required
def orders():
    db = get_db()
    user = current_user()
    rows = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user["id"],)
    ).fetchall()
    import json
    parsed_orders = []
    for row in rows:
        parsed_orders.append({**dict(row), "items": json.loads(row["items_json"])})
    return render_template("orders.html", orders=parsed_orders)


# ----------------------------------------------------------------------
# ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
