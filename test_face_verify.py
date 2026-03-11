from identity import verify_face

username = input("Enter username for verification: ")

if verify_face(username):
    print("Face verified successfully.")
else:
    print("Face verification failed.")