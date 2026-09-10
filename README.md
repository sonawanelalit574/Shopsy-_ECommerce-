# Shopsy 🛒

A Shopsy-like e-commerce website built with **Flask + SQLite**, combining
quick-commerce grocery delivery (15-minute promise) with a full general
marketplace (mobiles, electronics, fashion, home, beauty, books) — plus
smart payments (Cash on Delivery, UPI, Card).

## Features

- 🏠 Professional homepage with hero banner, quick-delivery grocery rail, category tiles, and featured products
- ⚡ "Quick Delivery" badge (15 minutes) automatically applied to Grocery & Fruits/Vegetables categories
- 🔍 Search across all products
- 🛍️ Product detail pages with images, price, stock, ratings, and related products
- 🛒 Session-based cart (add / increase / decrease / remove) with live AJAX badge updates
- 👤 User registration & login (secure password hashing)
- 💳 Smart Payments at checkout: **Cash on Delivery**, **UPI**, **Card**
- 📦 Order placement with delivery-type detection (quick vs standard) and ETA
- 🧾 Order history page per user
- 📱 Fully responsive, professional custom UI (no template look-alikes)

## Project structure

```
shopsy/
├── app.py                  # Flask backend — all routes & logic (Step 1)
├── requirements.txt        # Python dependencies
├── shopsy.db                # Auto-created SQLite database (after first run)
├── templates/               # Jinja2 HTML templates (Step 2)
│   ├── base.html            # Shared layout: header, nav, footer
│   ├── index.html           # Homepage
│   ├── category.html        # Category listing
│   ├── product.html         # Product detail page
│   ├── _product_card.html   # Reusable product card partial
│   ├── cart.html            # Cart page
│   ├── checkout.html        # Checkout + payment selection
│   ├── order_success.html   # Order confirmation
│   ├── orders.html          # Order history
│   ├── login.html
│   └── register.html
└── static/
    ├── css/style.css        # Full custom design system (Step 3)
    └── js/script.js         # AJAX add-to-cart (Step 4)
```

## How to run it — step by step

**Step 1 — Install Python** (3.9+ recommended). Check with:
```bash
python --version
```

**Step 2 — Install dependencies:**
```bash
cd shopsy
pip install -r requirements.txt
```

**Step 3 — Run the app:**
```bash
python app.py
```
The first run automatically creates `shopsy.db` and seeds it with 30+ sample products
across 8 categories.

**Step 4 — Open your browser:**
```
http://127.0.0.1:5000
```

**Step 5 — Try the flow:**
1. Browse the homepage — grocery items show a ⚡ "15 min" badge.
2. Add a few items to your cart.
3. Click **Cart** → **Proceed to Checkout**.
4. Register/log in if prompted.
5. Enter a delivery address, pick **Cash on Delivery**, **UPI**, or **Card**, and place the order.
6. View it under **My Orders**.

## Extending this into production

- Replace the placeholder product images (`placehold.co` URLs in `app.py`) with real
  product photography hosted on S3/Cloudinary.
- Wire the `upi` / `card` branch in the `/checkout` route in `app.py` to a real
  payment gateway (Razorpay, Stripe, PayU, Paytm) and verify the transaction
  webhook before marking an order "Paid".
- Move from SQLite to PostgreSQL/MySQL for multi-user production traffic.
- Add an admin dashboard for managing inventory and order status.
- Add real-time order tracking (WebSockets) for the 15-minute delivery promise.
