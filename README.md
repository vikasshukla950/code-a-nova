# Crave — Food Delivery App

**Code-A-NOVA · Month 3 Task Assignment**

Crave is a responsive food delivery web app built with Flask and SQLite. Customers can discover nearby restaurants, filter by cuisine, browse restaurant menus, add dishes to a bag, update quantities, enter delivery details, and place an order. The app saves orders and line items to a local database and shows an order confirmation with delivery progress.

## Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The SQLite database (`food_delivery.db`) is created and seeded with sample restaurants and dishes on first run.

To use another database path, set `FOOD_APP_DATABASE`. Set `FLASK_SECRET_KEY` to a private random value before deploying beyond a local demo. This assignment app uses a demo pay-on-delivery checkout and does not process real payments.

## Main flow

1. Discover restaurants and filter by cuisine.
2. Open a menu and add dishes to your bag.
3. Change quantities or remove items in the bag.
4. Enter customer and delivery details and place the order.
5. View the saved order, itemized total, and delivery status steps.

## Project structure

```text
app.py                 Flask routes, SQLite schema, sample data, and order flow
templates/             Responsive pages for discovery, menu, cart, checkout, and order
static/style.css       Crave visual design and mobile layout
requirements.txt       Flask dependency
```
