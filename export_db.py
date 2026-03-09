import json
from database import SessionLocal
import models
from datetime import datetime

# Helper function to serialize datetime objects
def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def export_db_to_json():
    db = SessionLocal()
    try:
        orders = db.query(models.Order).all()
        
        export_data = []
        for order in orders:
            order_data = {
                "id": order.id,
                "customer_id": order.customer_id,
                "total_amount": order.total_amount,
                "timestamp": order.timestamp,
                "items": []
            }
            
            for item in order.items:
                order_data["items"].append({
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "price_per_unit": item.price_per_unit,
                    "quantity": item.quantity
                })
                
            export_data.append(order_data)
            
        with open("orders.json", "w") as f:
            json.dump(export_data, f, indent=4, default=datetime_handler)
            
        print(f"Successfully exported {len(orders)} orders to 'orders.json'")
        
    finally:
        db.close()

if __name__ == "__main__":
    export_db_to_json()
