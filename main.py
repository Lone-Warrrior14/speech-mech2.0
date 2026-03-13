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
    verify_face,
    get_user_id,
    get_user_role,
    delete_user,
    get_all_users_with_ids,
    delete_user_by_id
)
import sys
import os
import subprocess
import webbrowser

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

# Ensure media module can be found
media_path = os.path.join(os.path.dirname(__file__), 'media')
sys.path.append(media_path)
try:
    from backend import entertainment_mode
except ImportError as e:
    print(f"[{e}] -> Media module is not available.")
    entertainment_mode = None

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
authenticated_user_id = None
interaction_mode = "chat" # Default mode
current_rag_namespace = None
current_rag_path = None
rag_history = []  # To maintain context during RAG sessions

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
        authenticated_user_id = str(get_user_id(selected_user))
        speak(f"Authentication successful. Welcome {selected_user}.")

        # 🔹 SELECT MODE
        speak("What would you like to do? Say 'chat' for normal chat, 'R A G' for documents, 'code assist' for code tools, or 'entertainment' for media.")
        mode_selection = listen()
        if mode_selection:
            if any(phrase in mode_selection for phrase in ["entertainment", "media", "start entertainment", "play movies"]):
                if entertainment_mode:
                    speak("Entering Entertainment mode. I will list your movies and open the player.")
                    # Pass control over to entertainment_mode loop
                    try:
                        entertainment_mode()
                    except Exception as e:
                        speak("Entertainment mode ended with an error.")
                        print(f"Media error: {e}")
                    interaction_mode = "chat"
                    speak("Welcome back. Defaulting to normal chat mode.")
                else:
                    speak("Entertainment module is not available.")
                    interaction_mode = "chat"

            elif any(phrase in mode_selection for phrase in ["code assist", "start code assist", "open code assist", "launch code assist"]):
                speak("Starting Code Assist. Please wait a moment.")
                code_assist_path = os.path.join(os.path.dirname(__file__), "code_assists", "app.py")
                try:
                    subprocess.Popen(
                        [sys.executable, code_assist_path],
                        cwd=os.path.join(os.path.dirname(__file__), "code_assists")
                    )
                    import time as _time
                    _time.sleep(2)  # Give Flask a moment to start
                    webbrowser.open("http://127.0.0.1:5000")
                    speak("Code Assist is running. I have opened it in your browser. Defaulting to normal chat mode.")
                except Exception as e:
                    speak("Failed to start Code Assist.")
                    print(f"Code Assist Error: {e}")
                interaction_mode = "chat"

            elif "rag" in mode_selection or "r a g" in mode_selection or "document" in mode_selection:
                if generate_answer:
                    interaction_mode = "rag"
                    speak("RAG mode activated. Let's select your RAG folder.")
                    
                    user_rag_root = os.path.join(os.path.dirname(__file__), "RAG", "users", f"user_{authenticated_user_id}")
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
                        current_rag_namespace = f"user_{authenticated_user_id}_{folder_name}"
                        rag_history.clear()  # Reset history for a new folder
                        
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

        # 🔹 CODE ASSIST
        if any(phrase in command for phrase in ["code assist", "start code assist", "open code assist", "launch code assist"]):
            speak("Starting Code Assist. Please wait a moment.")
            code_assist_path = os.path.join(os.path.dirname(__file__), "code_assists", "app.py")
            try:
                subprocess.Popen(
                    [sys.executable, code_assist_path],
                    cwd=os.path.join(os.path.dirname(__file__), "code_assists")
                )
                import time as _time
                _time.sleep(2)  # Give Flask a moment to start
                webbrowser.open("http://127.0.0.1:5000")
                speak("Code Assist is running. I have opened it in your browser.")
            except Exception as e:
                speak("Failed to start Code Assist.")
                print(f"Code Assist Error: {e}")
            continue

        # 🔹 ENTERTAINMENT / MEDIA
        if any(phrase in command for phrase in ["entertainment", "media", "start entertainment", "play movies"]):
            if entertainment_mode:
                speak("Entering Entertainment mode.")
                try:
                    entertainment_mode()
                except Exception as e:
                    speak("Entertainment mode ended with an error.")
                    print(f"Media error: {e}")
                speak("You have exited Entertainment mode.")
            else:
                speak("Entertainment module is not available.")
            continue
            
        if "delete user" in command or "remove user" in command:
            role = get_user_role(authenticated_user)
            if role and role.lower() == "admin":
                from identity import get_all_users_with_ids, delete_user_by_id
                users_list = get_all_users_with_ids()
                
                if not users_list:
                    speak("No users found in the system.")
                    continue
                    
                print("\n" + "="*40)
                print("       --- List of Users ---")
                print("="*40)
                for u in users_list:
                    print(f" ID: {u['id']} | Username: {u['username']}")
                print("="*40 + "\n")
                
                speak("I have printed the list of users in the terminal. Please type the exactly correct ID number of the user you want to delete.")
                import builtins
                user_id_input = builtins.input("Enter exact user ID to delete: ").strip()
                
                if user_id_input.isdigit():
                    victim_id = int(user_id_input)
                    target_user = next((u for u in users_list if u['id'] == victim_id), None)
                    
                    if target_user:
                        target_username = target_user['username']
                        if delete_user_by_id(victim_id):
                            speak(f"User {target_username} has been successfully deleted from the database.")
                            # Securely wipe their local RAG directory
                            import shutil
                            victim_rag_dir = os.path.join(os.path.dirname(__file__), "RAG", "users", f"user_{victim_id}")
                            if os.path.exists(victim_rag_dir):
                                try:
                                    shutil.rmtree(victim_rag_dir)
                                    print(f"Deleted folder {victim_rag_dir}")
                                    speak("And their local R A G files have been destroyed.")
                                except Exception as e:
                                    print(f"Error removing folder: {e}")
                                    speak("However, I encountered an error removing their local files.")
                            else:
                                speak("No local document directory existed for them.")
                        else:
                            speak(f"Database error. Failed to delete user {target_username}.")
                    else:
                        speak(f"User ID {victim_id} does not exist in the system.")
                else:
                    speak("Invalid ID entered. Deletion cancelled.")
            else:
                speak("Access Denied. You do not have administrator privileges to delete users.")
            continue

        if interaction_mode == "rag" and generate_answer:
            speak("Searching documents...")
            try:
                answer = generate_answer(command, namespace=current_rag_namespace, chat_history=rag_history)
                speak(answer)
                
                # Keep history for context
                rag_history.append({"user": command, "assistant": answer})
                rag_history = rag_history[-5:]  # Keep last 5 turns
                
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