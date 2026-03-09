from typing import Dict
from pydantic import BaseModel
from sqlalchemy.orm import Session
import models

class Product(BaseModel):
    id: str
    name: str
    price: float

class CartItem(BaseModel):
    product: Product
    quantity: int

class Cart(BaseModel):
    customer_id: str
    items: Dict[str, CartItem] = {}
    total: float = 0.0

# Mock product database
PRODUCT_DB = {
    "chips": Product(id="chips", name="Potato Chips", price=2.50),
    "soda": Product(id="soda", name="Cola", price=1.50),
    "candy": Product(id="candy", name="Candy Bar", price=1.00)
}

# In-memory cart store
carts: Dict[str, Cart] = {}

def get_or_create_cart(customer_id: str) -> Cart:
    if customer_id not in carts:
        carts[customer_id] = Cart(customer_id=customer_id)
    return carts[customer_id]

def add_product(customer_id: str, product_id: str) -> Cart:
    cart = get_or_create_cart(customer_id)
    product = PRODUCT_DB.get(product_id)
    if not product:
        return cart
    
    if product_id in cart.items:
        cart.items[product_id].quantity += 1
    else:
        cart.items[product_id] = CartItem(product=product, quantity=1)
    
    # Recalculate total to avoid floating point drift
    cart.total = sum(item.product.price * item.quantity for item in cart.items.values())
    return cart

def remove_product(customer_id: str, product_id: str) -> Cart:
    cart = get_or_create_cart(customer_id)
    if product_id in cart.items:
        item = cart.items[product_id]
        if item.quantity > 1:
            item.quantity -= 1
        else:
            del cart.items[product_id]
        
    # Recalculate total to avoid floating point drift
    cart.total = sum(item.product.price * item.quantity for item in cart.items.values())
    return cart

def checkout_cart(customer_id: str, db: Session) -> models.Order:
    cart = get_or_create_cart(customer_id)
    if not cart.items:
        return None

    # Check if customer exists in DB, if not create
    db_customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not db_customer:
        db_customer = models.Customer(id=customer_id)
        db.add(db_customer)
        db.commit()

    # Create the Order
    db_order = models.Order(customer_id=customer_id, total_amount=cart.total)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create Order Items
    for item_id, item_data in cart.items.items():
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item_data.product.id,
            product_name=item_data.product.name,
            price_per_unit=item_data.product.price,
            quantity=item_data.quantity
        )
        db.add(db_item)
    
    db.commit()

    # Clear the in-memory cart
    if customer_id in carts:
        del carts[customer_id]

    return db_order
