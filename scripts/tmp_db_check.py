import mysql.connector
import os
from dotenv import load_dotenv

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(root_dir, '.env'))

conn = mysql.connector.connect(
    host='127.0.0.1',
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    port=3306
)

cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT username, face_encoding FROM users')
for row in cursor.fetchall():
    has_face = row['face_encoding'] is not None
    print(f"User: {row['username']}, Has Face: {has_face}")
cursor.close()
conn.close()
