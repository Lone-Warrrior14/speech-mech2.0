from authorization.identity import get_all_usernames, get_user_role
import os

try:
    print("Fetching usernames...")
    users = get_all_usernames()
    print("Usernames:", users)
    
    if users:
        role = get_user_role(users[0])
        print(f"Role for {users[0]}: {role}")
    
    print("DONE: Identity module migration verified.")
except Exception as e:
    print("ERROR: Migration Test Failed:", e)
