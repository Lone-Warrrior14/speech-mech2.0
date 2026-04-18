import os
from datetime import datetime

# 🔹 Application Configuration
APPS = {
    "chrome": {
        "open": "start chrome",
        "process": "chrome.exe"
    },
    "edge": {
        "open": "start msedge",
        "process": "msedge.exe"
    },
    "notepad": {
        "open": "start notepad",
        "process": "notepad.exe"
    },
    "calculator": {
        "open": "start calc",
        "process": "CalculatorApp.exe"
    }
}

def route_intent(intent, command):
    command = command.strip().lower()

    # 🔹 HIGH-PRIORITY MODULE NAVIGATION (Check Keywords with Navigation Verbs)
    nav_verbs = ["go to", "open", "access", "start", "switch to", "launch", "initiate", "play"]
    
    def is_nav(cmd, keywords):
        cmd_low = cmd.lower()
        # Direct match
        if cmd_low in keywords: return True
        # Verb + keyword match
        for verb in nav_verbs:
            for kw in keywords:
                if f"{verb} {kw}" in cmd_low: return True
        return False

    # 📁 RAG Folder Selection (Higher Priority than generic nav)
    if any(x in command for x in ["select folder", "folder ", "select "]) and not any(x in command for x in ["create", "new", "make"]):
        folder_target = command.replace("select folder", "").replace("select", "").replace("folder", "").replace("directory", "").strip()
        if folder_target and len(folder_target) > 1:
            return f"FOLDER_SELECT:{folder_target}"
    
    # 📁 RAG Folder Creation
    if any(x in command for x in ["create folder", "new folder", "make folder", "create ", "new "]) or command.startswith("+folder"):
        folder_name = command.replace("+folder", "").replace("create folder", "").replace("new folder", "").replace("make folder", "").replace("create", "").replace("new", "").replace("folder", "").strip()
        if folder_name and len(folder_name) > 1:
            return f"CREATE_FOLDER:{folder_name}"


    if is_nav(command, ["rag", "intel", "rag intel"]):
        return "NAV:RAG"
    if is_nav(command, ["media", "entertainment", "movie", "video", "media box"]):
        # Support both "play movie X" and "play X"
        if command.startswith("play"):
            target = command.replace("play movie", "").replace("play", "").strip()
            if target:
                return f"PLAY_MOVIE:{target}"
        return "NAV:MEDIA"

    if is_nav(command, ["image", "visual", "manifest", "image gen", "visualizer"]):
        return "NAV:IMAGE_GEN"
    if is_nav(command, ["code", "omni", "coder", "omni coder", "code assistant"]):
        return "NAV:CODE"
    if is_nav(command, ["setting", "profile", "password", "face"]):
        return "NAV:SETTINGS"
    if is_nav(command, ["logout", "sign out"]):
        return "NAV:LOGOUT"
    if is_nav(command, ["dashboard", "main", "go back"]):
        return "NAV:DASHBOARD"

    # 🔹 NAVIGATION INTENT (LLM Detected)
    if intent == "navigation" or "go back" in command or "return to main" in command:
        # Fallback if keywords missed
        if "rag" in command: return "NAV:RAG"
        if "media" in command: return "NAV:MEDIA"
        return "NAV:DASHBOARD"
    
    if "upload" in command or "pick files" in command:
        return "CMD:UPLOAD"



    # 🔹 OPEN / START APPLICATIONS
    for trigger in ["open ", "start "]:
        if command.startswith(trigger):
            app_name = command.replace(trigger, "").strip()
            if app_name in APPS:
                os.system(APPS[app_name]["open"])
                return f"Opening {app_name}."
            
            # Special case for web modules via "open"
            if "rag" in app_name: return "NAV:RAG"
            if "media" in app_name: return "NAV:MEDIA"
            if "code" in app_name: return "NAV:CODE"
            if "image" in app_name or "visual" in app_name: return "NAV:IMAGE_GEN"
            if "setting" in app_name or "profile" in app_name or "password" in app_name: return "NAV:SETTINGS"
            if "logout" in app_name or "sign out" in app_name: return "NAV:LOGOUT"

    # 🔹 CLOSE APPLICATIONS
    if command.startswith("close "):
        app_name = command.replace("close ", "").strip()
        if app_name in APPS:
            process_name = APPS[app_name]["process"]
            os.system(f"taskkill /IM {process_name} /F")
            return f"Closing {app_name}."
    
    if intent == "image_gen":
        prompt = command.replace("generate", "").replace("create", "").replace("make", "").replace("image", "").replace("picture", "").replace("of ", "").replace("a ", "").replace("an ", "").strip()
        return f"GEN_IMAGE:{prompt}"

    # 🔹 TIME
    if intent == "ask_time":
        return f"The current time is {datetime.now().strftime('%H:%M')}"

    # 🔹 DATE
    if intent == "ask_date":
        return f"Today's date is {datetime.now().strftime('%Y-%m-%d')}"

    return None