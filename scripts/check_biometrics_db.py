import os
import sys
import pickle
from dotenv import load_dotenv

# Re-route to root .env
root_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(root_dir, ".env"))

import pyodbc
try:
    az_server = os.getenv("az_server")
    az_database = os.getenv("az_database")
    az_username = os.getenv("az_username")
    az_password = os.getenv("az_password")
    
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={az_server};"
        f"DATABASE={az_database};"
        f"UID={az_username};"
        f"PWD={az_password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, face_encoding FROM users")
    users = cursor.fetchall()
    
    print(f"Total Users: {len(users)}")
    for u in users:
        has_face = bool(u.face_encoding)
        print(f"User: {u.username} | Has Face: {has_face}")
        if has_face:
            try:
                enc = pickle.loads(bytes.fromhex(u.face_encoding))
                print(f"  Encoding valid (size: {len(enc)})")
            except Exception as e:
                print(f"  Encoding INVALID: {e}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
