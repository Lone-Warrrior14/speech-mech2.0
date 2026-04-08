from identity import get_connection

conn = get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM users")
for row in cursor.fetchall():
    print(row)
cursor.close()
conn.close()
