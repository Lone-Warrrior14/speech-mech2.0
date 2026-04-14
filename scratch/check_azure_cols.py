import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

az_server = os.getenv("az_server")
az_database = os.getenv("az_database")
az_username = os.getenv("az_username")
az_password = os.getenv("az_password")

try:
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={az_server};"
        f"DATABASE={az_database};"
        f"UID={az_username};"
        f"PWD={az_password};"
        f"Encrypt=yes;"
        f"TrustServerCertificate=yes;"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 * FROM users")
    columns = [column[0] for column in cursor.description]
    print("Columns:", columns)
    conn.close()
except Exception as e:
    print("Error:", e)
