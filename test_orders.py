import asyncio
import json
from fastapi.testclient import TestClient
from main import app
from database import get_db, engine
import cart
from database import engine
import models

# Recreate DB for test
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_order_history():
    # 1. Add some items to cart
    c = cart.get_or_create_cart("user_test")
    cart.add_product("user_test", "chips")
    cart.add_product("user_test", "chips")
    cart.add_product("user_test", "soda")
    
    # 2. Checkout
    resp = client.post("/api/checkout/user_test")
    assert resp.status_code == 200
    
    # 3. Add more items
    cart.add_product("user_test", "candy")
    resp2 = client.post("/api/checkout/user_test")
    assert resp2.status_code == 200
    
    # 4. Get history
    history_resp = client.get("/api/orders/user_test")
    assert history_resp.status_code == 200
    
    orders = history_resp.json()
    print("ORDERS RETURNED:")
    print(json.dumps(orders, indent=2))
    assert len(orders) == 2
    
    # The first one returned should be the second order (most recent because of timestamp.desc())
    assert orders[0]["total_amount"] == 1.50 # Candy is 1.50
    assert len(orders[0]["items"]) == 1
    assert orders[0]["items"][0]["product_id"] == "candy"

    assert orders[1]["total_amount"] == (2.50 * 2) + 1.20 # chips(2.5)*2 + soda(1.2) = 6.20
    assert len(orders[1]["items"]) == 2
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_order_history()
