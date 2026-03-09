import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('billing.db')
cursor = conn.cursor()

print('=== DATABASE TABLES ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f'Table: {table[0]}')

print('\n=== ORDERS DATA ===')
cursor.execute('SELECT * FROM orders ORDER BY timestamp DESC')
orders = cursor.fetchall()
for order in orders:
    print(f'Order ID: {order[0]}, Customer: {order[1]}, Total: ${order[2]:.2f}, Time: {order[3]}')

print('\n=== ORDER ITEMS DATA ===')
cursor.execute('SELECT * FROM order_items ORDER BY order_id DESC')
items = cursor.fetchall()
for item in items:
    print(f'Order {item[1]}: {item[3]} (x{item[5]}) - ${item[4]:.2f} each')

print('\n=== CUSTOMERS DATA ===')
cursor.execute('SELECT * FROM customers')
customers = cursor.fetchall()
for customer in customers:
    print(f'Customer ID: {customer[0]}, Name: {customer[1] or "N/A"}')

conn.close()