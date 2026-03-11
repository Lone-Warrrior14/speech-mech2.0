import bcrypt

password = input("Enter password to hash: ").encode()

hashed = bcrypt.hashpw(password, bcrypt.gensalt())

print("Hashed password:")
print(hashed.decode())