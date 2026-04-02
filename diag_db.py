import os
import sys
from dotenv import load_dotenv

# Re-route to root .env
root_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(root_dir, ".env"))

print(f"DB_USER: {os.getenv('DB_USER')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")

try:
    import mysql.connector
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=3306
    )
    print("Database connection SUCCESSFUL.")
    conn.close()
except Exception as e:
    print(f"Database connection FAILED: {e}")
