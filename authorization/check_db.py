from identity import get_all_usernames
try:
    users = get_all_usernames()
    print(f"Users in DB: {users}")
except Exception as e:
    print(f"Error: {e}")
