from speech_to_text import listen
from text_to_speech import speak
from assistant import ask_ai, reset_memory, get_full_response
from command_router import route_intent
from intent_detector import detect_intent
from identity import (
    fuzzy_match_user,
    verify_password,
    switch_active_user,
    get_password_hash,
    set_user_password,
    create_user,
    register_face,
    verify_face
)
import time
import sys
import getpass

TIMEOUT_SECONDS = 30

def should_exit(command):
    return any(phrase in command for phrase in [
        "exit control",
        "stop assistant",
        "shutdown assistant"
    ])

print("Wake word system active...")

authenticated_user = None

while True:

    command = listen(prompt="Waiting for wake word (or type 'hello control')...")

    if not command:
        continue

    if should_exit(command):
        speak("Shutting down. Goodbye.")
        sys.exit()

    if "hello" not in command or "control" not in command:
        continue

    # 🔹 If already authenticated, skip login
    if authenticated_user:
        speak("Yes, I am here.")

    else:

        # 🔐 IDENTIFICATION STAGE
        speak("Who are you? Say I am followed by your name.(better if you type your username)")

        name_input = listen()

        if not name_input:
            speak("I did not hear your name.")
            continue

        if should_exit(name_input):
            speak("Shutting down. Goodbye.")
            sys.exit()

        if "i am" in name_input:
            spoken_name = name_input.split("i am", 1)[1].strip()
        else:
            spoken_name = name_input.strip()

        if not spoken_name:
            speak("I could not detect your name.")
            continue

        matches = fuzzy_match_user(spoken_name)

        if len(matches) == 0:
            speak("User not recognized. Would you like to register?")
            reg_choice = listen()
            if reg_choice and ("yes" in reg_choice or "register" in reg_choice):
                print("Registration mode triggered.")
                new_user = input("Enter new username: ").strip()
                if not new_user:
                    speak("Username cannot be empty. Registration aborted.")
                    continue
                
                success = create_user(new_user)
                if not success:
                    speak("User already exists or database error occurred.")
                    continue
                
                speak(f"User {new_user} created. Say, I want to use my face, or, I want to use a password.")
                method = listen()
                if method and "face" in method:
                    speak("Starting face registration.")
                    register_face(new_user)
                else:
                    speak("Please type your new password in the terminal.")
                    new_password = getpass.getpass("Create Password: ")
                    if new_password:
                        set_user_password(new_user, new_password)
                        speak("Password created successfully.")
                    else:
                        speak("Skipping password creation.")
                
                speak(f"Registration complete. Please log in again, {new_user}.")
            else:
                speak("Registration cancelled.")
            continue

        if len(matches) == 1:
            selected_user = matches[0]
            speak(f"I identified you as {selected_user}.")
        else:
            speak("I found multiple matches.")
            for i, user in enumerate(matches, start=1):
                speak(f"Option {i}: {user}")

            speak("Say, I choose option one, or, I choose option two.")

            selection = listen()

            if not selection:
                speak("No selection detected.")
                continue

            if should_exit(selection):
                speak("Shutting down. Goodbye.")
                sys.exit()

            if "one" in selection or "1" in selection:
                selected_user = matches[0]
            elif "two" in selection or "2" in selection:
                selected_user = matches[1]
            else:
                speak("Invalid selection.")
                continue

            speak(f"You selected {selected_user}.")

        # 🔐 AUTHENTICATION
        stored_hash = get_password_hash(selected_user)
        
        speak("Initiating face verification. Please look at the camera.")
        auth_success = False
        
        if verify_face(selected_user):
            auth_success = True
        else:
            speak("Face verification failed. Falling back to password.")
            if not stored_hash:
                speak("No password found. Please create a new password.")
                new_password = getpass.getpass("Create Password: ")
                if not new_password:
                    speak("Password cannot be empty.")
                    continue
                set_user_password(selected_user, new_password)
                speak("Password created successfully.")
                auth_success = True
            else:
                speak("Enter your password in the terminal.")
                password = getpass.getpass("Password: ")
                if verify_password(selected_user, password):
                    auth_success = True
                    
        if not auth_success:
            speak("Authentication failed.")
            continue

        # 🔐 AUTH SUCCESS
        switch_active_user(selected_user)
        authenticated_user = selected_user
        speak(f"Authentication successful. Welcome {selected_user}.")

    last_activity = time.time()

    # 🔹 SESSION LOOP
    while True:

        if time.time() - last_activity > TIMEOUT_SECONDS:
            print("Assistant sleeping. Say 'hello control' to wake.")
            break

        command = listen()

        if not command:
            continue

        last_activity = time.time()

        if should_exit(command):
            speak("Shutting down. Goodbye.")
            sys.exit()

        if "expand" in command:
            full = get_full_response()
            if full:
                speak(full)
            continue

        intent = detect_intent(command)
        response = route_intent(intent, command)

        if response:
            speak(response)
        else:
            reply = ask_ai(command)
            speak(reply)