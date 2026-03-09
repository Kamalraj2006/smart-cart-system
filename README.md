# Smart Cart — Cashier-less Billing System

A real-time, camera-based billing system where picking up a product automatically adds its price to the customer's bill — no cashier required.

> **Note:** The current version uses QR code scanning as a prototype for product detection. Full AI-based pick-up detection (using object detection models like YOLO) will be implemented in a future version.

---

## Features

- 📷 **Live Camera Scanning** — Uses the device camera to detect QR codes in real time
- 🛒 **Automatic Cart Updates** — Items are added/removed instantly via WebSocket
- 💳 **Checkout & Order History** — Saves orders to a local SQLite database
- 🧪 **Manual Testing Controls** — Add/remove items manually without a camera or QR code
- 🌐 **Web Frontend** — Responsive UI with glassmorphism design

---

## Project Structure

```
project resource 2/
├── backend/
│   ├── main.py          # FastAPI app — all API & WebSocket routes
│   ├── cart.py          # Cart logic (add, remove, checkout)
│   ├── models.py        # SQLAlchemy DB models (Customer, Order, OrderItem)
│   ├── database.py      # DB engine & session setup (SQLite)
│   ├── vision.py        # QR code detection via OpenCV
│   ├── export_db.py     # Export orders to orders.json
│   ├── view_db.py       # Print DB contents to terminal
│   ├── test_orders.py   # Integration test for order history
│   └── requirements.txt
└── frontend/
    ├── index.html       # App shell & layout
    ├── app.js           # All frontend logic (camera, WebSocket, cart UI)
    └── style.css        # Glassmorphism dark theme
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, WebSocket |
| Database | SQLite via SQLAlchemy |
| Vision | OpenCV (`cv2`) QR Code Detector |
| Frontend | Vanilla HTML, CSS, JavaScript |

---

## Setup & Installation

### 1. Create and activate a virtual environment

```bash
cd "backend"
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the backend server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### 4. Open the frontend

Open `frontend/index.html` directly in your browser, or serve it with any static file server.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/api/products` | List all products |
| `GET` | `/api/cart/{customer_id}` | Get cart for a customer |
| `POST` | `/api/cart/{customer_id}/add/{product_id}` | Manually add item |
| `POST` | `/api/cart/{customer_id}/remove/{product_id}` | Manually remove item |
| `POST` | `/api/checkout/{customer_id}` | Checkout and save order |
| `GET` | `/api/orders/{customer_id}` | Get order history |
| `WS` | `/ws/camera/{customer_id}` | WebSocket for live camera frames |

---

## QR Code Format (Current Prototype)

In the current version, each product has a QR code. The camera scans it to detect a pick-up or put-back action. QR codes must encode text in the following format:

```
ADD:chips
REMOVE:soda
```

Supported product IDs: `chips`, `soda`, `candy`

> **Future:** QR codes will be replaced by an AI object detection model that automatically recognises which product a customer picks up or puts back — no QR codes needed.

---

## Utility Scripts

```bash
# View all database records in the terminal
python view_db.py

# Export all orders to orders.json
python export_db.py

# Run integration tests
python test_orders.py
```

---

## How It Works

1. Customer enters their ID on the login screen.
2. The app opens a WebSocket connection and starts the camera.
3. Every 500ms, a JPEG frame is sent to the backend.
4. The backend uses OpenCV to detect QR codes in each frame.
5. If a valid QR is found (e.g. `ADD:chips`), the cart is updated and the new state is broadcast back via WebSocket.
6. On checkout, the order is saved to the SQLite database and the cart is cleared.
