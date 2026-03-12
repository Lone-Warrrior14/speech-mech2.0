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
import sys
import os

# Ensure RAG module can be found if running from root directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'RAG'))
try:
    from RAG.rag_answer import generate_answer
    from RAG.universal_reader import pick_and_read_files
    from RAG.insert_pinecone import insert_document
except ImportError as e:
    # Handle scenario where RAG is missing or not installed
    print(f"[{e}] -> RAG module is not available. Some dependencies might be missing.")
    generate_answer = None
    pick_and_read_files = None
    insert_document = None

import time
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
interaction_mode = "chat" # Default mode
current_rag_namespace = None
current_rag_path = None

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

        # 🔹 SELECT MODE
        speak("What would you like to do? Say 'chat' for normal chat, or 'R A G' for document question answering.")
        mode_selection = listen()
        if mode_selection:
            if "rag" in mode_selection or "r a g" in mode_selection or "document" in mode_selection:
                if generate_answer:
                    interaction_mode = "rag"
                    speak("RAG mode activated. Let's select your RAG folder.")
                    
                    user_rag_root = os.path.join(os.path.dirname(__file__), "RAG", "users", authenticated_user)
                    os.makedirs(user_rag_root, exist_ok=True)
                    
                    folders = [f for f in os.listdir(user_rag_root) if os.path.isdir(os.path.join(user_rag_root, f))]
                    if folders:
                        print("Available folders:", ", ".join(folders))
                        speak("I see existing folders. Please type the name of the folder you want to create or use in the terminal.")
                    else:
                        speak("No folders found. Let's create a new one. Please type the folder name in the terminal.")
                        
                    import builtins
                    folder_name = builtins.input(f"Enter RAG folder name (Available: {', '.join(folders)} or type new name): ").strip()
                    
                    if folder_name:
                        current_rag_path = os.path.join(user_rag_root, folder_name)
                        os.makedirs(current_rag_path, exist_ok=True)
                        current_rag_namespace = f"{authenticated_user}_{folder_name}"
                        
                        speak(f"Folder {folder_name} selected. Do you want to upload files into this folder, or just chat?")
                        action = listen()
                        if action and ("upload" in action or "add" in action or "new" in action or "yes" in action):
                            speak("Please select the documents from the popup window.")
                            try:
                                results = pick_and_read_files()
                                if results:
                                    speak("Files parsed successfully. Updating your database.")
                                    for file_path, text in results:
                                        filename = os.path.basename(file_path)
                                        # Index tightly coupled to their namespace
                                        insert_document(filename, text, namespace=current_rag_namespace)
                                        
                                        # Store locally in their user box just as txt
                                        txt_dest = os.path.join(current_rag_path, filename + ".txt")
                                        with open(txt_dest, "w", encoding="utf-8") as f:
                                            f.write(text)
                                            
                                    speak(f"Successfully uploaded {len(results)} documents. You can now prompt me questions.")
                                else:
                                    speak("No documents selected.")
                                    interaction_mode = "chat"
                                    speak("Falling back to normal chat.")
                            except Exception as e:
                                print(f"File Add Error: {e}")
                                speak("I encountered an error trying to process the files.")
                        else:
                            speak("Okay, chatting with your existing documents in this folder. Go ahead and start asking.")
                    else:
                        speak("No folder entered. Falling back to normal chat.")
                        interaction_mode = "chat"
                else:
                    speak("RAG module is not available. Falling back to normal chat.")
            else:
                interaction_mode = "chat"
                speak("Normal chat mode activated.")
        else:
            speak("No mode selected, defaulting to normal chat.")

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

        if interaction_mode == "rag" and generate_answer:
            speak("Searching documents...")
            try:
                answer = generate_answer(command, namespace=current_rag_namespace)
                speak(answer)
                
                # Save the user's RAG question/answer pair locally to their dedicated folder instead of the cloud
                try:
                    timestamp_str = time.strftime("%Y%m%d-%H%M%S")
                    local_output = os.path.join(current_rag_path, "chat_history.txt")
                    
                    with open(local_output, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp_str}] Question: {command}\nAnswer:\n{answer}\n{'-'*40}\n")
                        
                    print(f"Appended RAG answer to: {local_output}")
                except Exception as local_save_error:
                    print(f"Failed to save locally: {local_save_error}")
                        
            except Exception as e:
                speak("I encountered an error querying the documents.")
                print(f"RAG Error: {e}")
        else:
            intent = detect_intent(command)
            response = route_intent(intent, command)

            if response:
                speak(response)
            else:
                reply = ask_ai(command)
                speak(reply)