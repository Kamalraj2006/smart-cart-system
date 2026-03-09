from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import asyncio
import json

import cart
import vision
import database
import models
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(title="Cashier-less Billing System Backend")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# In production, configure this properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections per customer
active_connections: Dict[str, WebSocket] = {}

class CartResponse(BaseModel):
    cart: cart.Cart

@app.get("/")
def read_root():
    return {"message": "Cashier-less Billing API is running"}

@app.get("/api/products")
def get_products():
    return cart.PRODUCT_DB

@app.get("/api/cart/{customer_id}")
def get_cart(customer_id: str):
    return cart.get_or_create_cart(customer_id)

async def notify_cart_update(customer_id: str, current_cart: cart.Cart):
    if customer_id in active_connections:
        ws = active_connections[customer_id]
        try:
            # Send latest cart state to specific customer
            await ws.send_json({"type": "cart_update", "cart": current_cart.model_dump()})
        except Exception as e:
            print(f"Error sending update to {customer_id}: {e}")

@app.post("/api/cart/{customer_id}/add/{product_id}")
async def add_item_manual(customer_id: str, product_id: str):
    """Manual endpoint for testing without camera"""
    if product_id not in cart.PRODUCT_DB:
        raise HTTPException(status_code=404, detail="Product not found")
    c = cart.add_product(customer_id, product_id)
    await notify_cart_update(customer_id, c)
    return c

@app.post("/api/cart/{customer_id}/remove/{product_id}")
async def remove_item_manual(customer_id: str, product_id: str):
    """Manual endpoint for testing without camera"""
    c = cart.remove_product(customer_id, product_id)
    await notify_cart_update(customer_id, c)
    return c

@app.post("/api/checkout/{customer_id}")
async def checkout(customer_id: str, db: Session = Depends(database.get_db)):
    """Checkout cart and save to database"""
    order = cart.checkout_cart(customer_id, db)
    if not order:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Notify frontend of empty cart after successful checkout
    empty_cart = cart.get_or_create_cart(customer_id)
    await notify_cart_update(customer_id, empty_cart)
    
    return {"message": "Checkout successful", "order_id": order.id, "total": order.total_amount}

@app.get("/api/orders/{customer_id}")
async def get_orders(customer_id: str, db: Session = Depends(database.get_db)):
    """Get past orders for a customer"""
    orders = db.query(models.Order).filter(models.Order.customer_id == customer_id).order_by(models.Order.timestamp.desc()).all()
    
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "total_amount": order.total_amount,
            "timestamp": order.timestamp.isoformat(),
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "price_per_unit": item.price_per_unit,
                    "quantity": item.quantity
                } for item in order.items
            ]
        })
    return result

@app.websocket("/ws/camera/{customer_id}")
async def camera_websocket(websocket: WebSocket, customer_id: str):
    await websocket.accept()
    active_connections[customer_id] = websocket
    print(f"Customer {customer_id} connected camera WebSocket")
    
    # Send initial cart state
    c = cart.get_or_create_cart(customer_id)
    await websocket.send_json({"type": "cart_update", "cart": c.model_dump()})
    
    try:
        last_processed_action = None
        last_processed_product = None
        no_qr_frames = 0
        
        while True:
            # Wait for frame bytes from frontend
            frame_bytes = await websocket.receive_bytes()
            
            action, product_id = vision.process_frame_for_actions(frame_bytes)
            
            if action and product_id and product_id in cart.PRODUCT_DB:
                no_qr_frames = 0
                if action != last_processed_action or product_id != last_processed_product:
                    print(f"Vision detected: {action} {product_id} for user {customer_id}")
                    if action == "ADD":
                        updated_cart = cart.add_product(customer_id, product_id)
                        await notify_cart_update(customer_id, updated_cart)
                    elif action == "REMOVE":
                        updated_cart = cart.remove_product(customer_id, product_id)
                        await notify_cart_update(customer_id, updated_cart)
                    
                    last_processed_action = action
                    last_processed_product = product_id
            else:
                # If we don't see anything for many frames, reset the debounce lock
                no_qr_frames += 1
                if no_qr_frames > 30: # Assuming ~30fps, 1 second of nothing resets the lock
                    last_processed_action = None
                    last_processed_product = None

    except WebSocketDisconnect:
        print(f"Customer {customer_id} disconnected")
        if customer_id in active_connections:
            del active_connections[customer_id]
