import os
import sys
import pickle
from dotenv import load_dotenv

# Re-route to root .env
root_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(root_dir, ".env"))

import mysql.connector
try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=3306
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username, face_encoding FROM users")
    users = cursor.fetchall()
    
    print(f"Total Users: {len(users)}")
    for u in users:
        has_face = bool(u['face_encoding'])
        print(f"User: {u['username']} | Has Face: {has_face}")
        if has_face:
            try:
                enc = pickle.loads(bytes.fromhex(u['face_encoding']))
                print(f"  Encoding valid (size: {len(enc)})")
            except Exception as e:
                print(f"  Encoding INVALID: {e}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
