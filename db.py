import pyodbc
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get values from .env
az_server = os.getenv("az_server")
az_database = os.getenv("az_database")
az_username = os.getenv("az_username")
az_password = os.getenv("az_password")

try:
    # Establish connection
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={az_server};"
        f"DATABASE={az_database};"
        f"UID={az_username};"
        f"PWD={az_password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )

    print("✅ Connected to Azure SQL\n")

    cursor = conn.cursor()

    # Execute query
    cursor.execute("SELECT * FROM users")

    rows = cursor.fetchall()

    print("📦 Users Data:\n")

    for row in rows:
        print(f"""
ID: {row.id}
Username: {row.username}
Greeting: {row.greeting}
Default: {row.is_default}
Password Hash: {row.password_hash}
Role: {row.role}
Approved: {row.is_approved}
---------------------------
""")

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ Error:", e)